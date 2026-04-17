import os
import torch
import numpy as np
import matplotlib
# Set backend to 'Agg' to prevent windows from popping up
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import itertools
import multiprocessing
from scipy.spatial import ConvexHull, QhullError

# ==========================================
# GPU ACCELERATED ANALYSIS (PyTorch)
# ==========================================

def get_triangle_counts_gpu(point_sets, batch_size=25000):
    """
    Scans millions of point sets on the GPU to count non-empty triangles.
    Automatically utilizes multiple GPUs if available.
    """
    num_gpus = torch.cuda.device_count()
    if num_gpus == 0:
        print("[!] No GPU found. Falling back to CPU (This will be very slow).")
        device_ids = [torch.device("cpu")]
    else:
        print(f"[+] Found {num_gpus} GPU(s). Splitting workload...")
        device_ids = [torch.device(f"cuda:{i}") for i in range(num_gpus)]

    num_sets, n, _ = point_sets.shape
    
    # 1. Pre-compute combinatorial metadata
    # C(n, 3) triangles
    tri_indices = list(itertools.combinations(range(n), 3))
    num_triangles = len(tri_indices)
    
    # Define edges for orientation checks
    edges = []
    for i in range(n):
        for j in range(n):
            if i != j: edges.append((i, j))
    edge_map = {edge: i for i, edge in enumerate(edges)}
    
    # Map each triangle's 3 edges to their indices in the edge list
    tri_edge_map = []
    for i, j, k in tri_indices:
        tri_edge_map.append([edge_map[(i,j)], edge_map[(j,k)], edge_map[(k,i)]])
    
    # 2. Main Logic: Shard across GPUs
    def process_shard(device, shard_sets):
        # Move static metadata to this GPU
        e_idx = torch.tensor(edges, device=device)
        te_idx = torch.tensor(tri_edge_map, device=device)
        
        shard_counts = []
        for i in range(0, len(shard_sets), batch_size):
            end = min(i + batch_size, len(shard_sets))
            # Convert to float32 for speed. If coordinates are very large (e.g. b16), consider float64.
            batch = torch.from_numpy(shard_sets[i:end].astype(np.float32)).to(device)
            
            # Compute orientations: sign(P1, P2, P3) = (x1-x3)(y2-y3) - (x2-x3)(y1-y3)
            # P1, P2 are the edge vertices, P3 are ALL points in the set
            p1 = batch[:, e_idx[:, 0], :].unsqueeze(2) # (B, E, 1, 2)
            p2 = batch[:, e_idx[:, 1], :].unsqueeze(2) # (B, E, 1, 2)
            p3 = batch.unsqueeze(1).expand(-1, e_idx.shape[0], -1, -1) # (B, E, N, 2)
            
            # (x1-x3)(y2-y3) - (x2-x3)(y1-y3)
            signs = (p1[...,0]-p3[...,0])*(p2[...,1]-p3[...,1]) - \
                    (p2[...,0]-p3[...,0])*(p1[...,1]-p3[...,1]) # (B, E, N)
            
            # Triangle inclusion check: look up signs for the 3 edges of every triangle
            s1 = signs[:, te_idx[:, 0], :] # (B, T, N)
            s2 = signs[:, te_idx[:, 1], :] # (B, T, N)
            s3 = signs[:, te_idx[:, 2], :] # (B, T, N)
            
            # P is strictly inside triangle if all 3 signs have the same non-zero direction
            is_inside = ((s1 > 1e-5) & (s2 > 1e-5) & (s3 > 1e-5)) | \
                        ((s1 < -1e-5) & (s2 < -1e-5) & (s3 < -1e-5)) # (B, T, N)
            
            # Triangle is non-empty if ANY point is inside it
            non_empty_mask = is_inside.any(dim=2) # (B, T)
            
            # Count non-empty triangles per config in batch
            batch_counts = non_empty_mask.sum(dim=1).cpu().numpy()
            shard_counts.append(batch_counts)
            
            if (i // batch_size) % 10 == 0:
                print(f"    [GPU {device}] Progress: {end}/{len(shard_sets)}...")
                
        return np.concatenate(shard_counts) if shard_counts else np.array([], dtype=np.int64)

    # Use multiprocessing only to launch kernels on separate GPUs if needed, 
    # but for a single script sequential shard processing is often easier to debug.
    # We will process each GPU shard sequentially here for robustness.
    shards = np.array_split(point_sets, len(device_ids))
    final_counts_list = []
    
    for i, dev in enumerate(device_ids):
        print(f"[+] Starting shard on {dev}...")
        res = process_shard(dev, shards[i])
        final_counts_list.append(res)

    return np.concatenate(final_counts_list)

# ==========================================
# PLOTTING LOGIC (CPU)
# ==========================================

def get_triangle_lists_cpu(points):
    """Accurate CPU-based triangle check for the final subset of plots."""
    n = len(points)
    pts = points.astype(np.int64)
    def sign(p1, p2, p3):
        return (int(p1[0])-int(p3[0]))*(int(p2[1])-int(p3[1])) - (int(p2[0])-int(p3[0]))*(int(p1[1])-int(p3[1]))

    empty_tris, non_empty_tris = [], []
    for i, j, k in itertools.combinations(range(n), 3):
        v1, v2, v3 = pts[i], pts[j], pts[k]
        is_empty = True
        for m in range(n):
            if m in (i, j, k): continue
            d1 = sign(pts[m], v1, v2)
            d2 = sign(pts[m], v2, v3)
            d3 = sign(pts[m], v3, v1)
            if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
                is_empty = False
                break
        triple = (i+1, j+1, k+1)
        if is_empty: empty_tris.append(triple)
        else: non_empty_tris.append(triple)
    return empty_tris, non_empty_tris

def render_plot(args):
    """Renders a single high-quality configuration plot."""
    rank, original_idx, points, calc_count, n_points, file_base, output_dir = args
    
    fig, ax = plt.subplots(figsize=(7, 7))
    
    # Draw Iterative Convex Hulls
    rem_points = points.copy()
    layer = 0
    colors = ['tab:red', 'tab:green', 'tab:orange', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:olive', 'tab:cyan']
    while len(rem_points) >= 3:
        try:
            hull = ConvexHull(rem_points)
            color = 'k' if layer == 0 else colors[layer % len(colors)]
            alpha = 0.3 if layer == 0 else 0.6
            for simplex in hull.simplices:
                ax.plot(rem_points[simplex, 0], rem_points[simplex, 1], color=color, linestyle='-', alpha=alpha, zorder=1)
            
            # Remove vertices of this hull
            mask = np.ones(len(rem_points), dtype=bool)
            mask[list(hull.vertices)] = False
            rem_points = rem_points[mask]
            layer += 1
        except QhullError: break

    # Plot points and annotations
    ax.scatter(points[:, 0], points[:, 1], c='blue', s=80, zorder=3)
    for i, (px, py) in enumerate(points):
        ax.text(px, py, f" {i+1}", fontsize=12, ha='left', va='center', fontweight='bold')

    # Re-calculate exact lists for display
    empty_tris, non_empty_tris = get_triangle_lists_cpu(points)
    
    ax.set_title(f"Type #{original_idx} (N={n_points})\nEmpty Triangles: {len(empty_tris)} | Non-Empty Triangles: {len(non_empty_tris)}")
    ax.axis('off')
    
    save_name = f"{len(non_empty_tris)}NET_{file_base}_{original_idx:06d}.png"
    plt.savefig(os.path.join(output_dir, save_name), bbox_inches='tight', dpi=150)
    plt.close(fig)

# ==========================================
# MAIN WORKFLOW
# ==========================================

def run_maximal_search(filepath):
    if not os.path.exists(filepath):
        print(f"[-] Error: File {filepath} not found.")
        return

    filename = os.path.basename(filepath)
    file_base = os.path.splitext(filename)[0]
    
    # Parse N from filename (e.g., otypes08.b08 -> 08)
    try:
        n_points = int(filename[6:8])
    except:
        print("[-] Error: Could not parse N from filename. Using N=8 default.")
        n_points = 8

    # Determine bit depth
    dtype = np.uint8 if filepath.endswith('.b08') else np.uint16

    print(f"[+] Loading {filename}...")
    with open(filepath, 'rb') as f:
        data = np.frombuffer(f.read(), dtype=dtype)
    
    try:
        point_sets = data.reshape(-1, n_points, 2)
    except ValueError:
        print("[-] Error: Data length does not match point count.")
        return

    total_sets = len(point_sets)
    print(f"[+] Successfully loaded {total_sets} configurations.")

    # STAGE 1: GPU SEARCH
    print("[*] Starting GPU-accelerated triangle counting...")
    counts = get_triangle_counts_gpu(point_sets)

    # STAGE 2: SELECTION (Find all with the absolute maximum)
    max_val = np.max(counts)
    top_indices = np.where(counts == max_val)[0]
    num_found = len(top_indices)
    
    print(f"[*] Analysis complete. Maximum non-empty triangles found: {max_val}")
    print(f"[*] Found {num_found} maximal configurations.")
    
    # STAGE 3: PLOTTING
    output_dir = f"maximal_configs_{file_base}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"[+] Saving {num_found} plots to ./{output_dir}/")

    plot_tasks = []
    for rank, idx in enumerate(top_indices, 1):
        plot_tasks.append((rank, idx, point_sets[idx], counts[idx], n_points, file_base, output_dir))

    # Use CPU parallelism for the final plotting stage
    with multiprocessing.Pool() as pool:
        pool.map(render_plot, plot_tasks)

    print(f"\n[DONE] Successfully analyzed {total_sets} sets and plotted all {num_found} maximal configurations.")

if __name__ == "__main__":
    # Change 'otypes08.b08' to 'otypes10.b16' etc.
    # Note: For N=10, the file is ~572MB, which fits easily in RAM.
    target = 'otypes09.b16' 
    run_maximal_search(target)
