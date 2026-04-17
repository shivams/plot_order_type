import matplotlib
# Set backend to 'Agg' to prevent windows from popping up (Headless mode)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import numpy as np
import os
import itertools
import multiprocessing
from scipy.spatial import ConvexHull, QhullError

def get_triangle_lists(points):
    """Returns lists of empty and non-empty triangles (1-indexed) in a given point set."""
    n = len(points)
    # Convert points to int64 to prevent overflow on subtraction/multiplication with uint16 types
    pts = points.astype(np.int64)
    
    def sign(p1, p2, p3):
        # Using pure Python int (from Numpy int64) which has unlimited precision - guarantees zero overflow
        x1, y1 = int(p1[0]), int(p1[1])
        x2, y2 = int(p2[0]), int(p2[1])
        x3, y3 = int(p3[0]), int(p3[1])
        return (x1 - x3) * (y2 - y3) - (x2 - x3) * (y1 - y3)

    empty_tris = []
    non_empty_tris = []

    for i, j, k in itertools.combinations(range(n), 3):
        v1, v2, v3 = pts[i], pts[j], pts[k]
        is_empty = True
        for m in range(n):
            if m == i or m == j or m == k:
                continue
            pt = pts[m]
            
            d1 = sign(pt, v1, v2)
            d2 = sign(pt, v2, v3)
            d3 = sign(pt, v3, v1)
            
            has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
            has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
            
            if not (has_neg and has_pos):
                is_empty = False
                break
                
        # 1-indexed to match plot annotations
        triple = (i+1, j+1, k+1)
        if is_empty:
            empty_tris.append(triple)
        else:
            non_empty_tris.append(triple)
            
    return empty_tris, non_empty_tris

def process_point_set(args):
    i, points, n_points, file_base, output_dir, show_triangles_list, iterative_hulls = args
    
    # Create Figure (don't show it)
    if show_triangles_list:
        fig, (ax, ax_text) = plt.subplots(1, 2, figsize=(10, 5), gridspec_kw={'width_ratios': [1, 1]})
    else:
        fig, ax = plt.subplots(figsize=(5, 5))
    
    # Draw Convex Hull(s)
    remaining_points = points.copy()
    layer = 0
    # Distinct colors for inner layers
    colors = ['tab:red', 'tab:green', 'tab:orange', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:olive', 'tab:cyan']
    
    # Randomly shuffle colors
    np.random.shuffle(colors)
    
    while len(remaining_points) >= 3:
        try:
            hull = ConvexHull(remaining_points)
            if layer == 0:
                color = 'k'
                alpha = 0.3
            else:
                color = colors[(layer - 1) % len(colors)]
                alpha = 0.6
                
            for simplex in hull.simplices:
                ax.plot(remaining_points[simplex, 0], remaining_points[simplex, 1], color=color, linestyle='-', alpha=alpha)
                
            if not iterative_hulls:
                break
                
            # Remove hull points to find the next layer
            hull_indices = set(hull.vertices)
            mask = np.ones(len(remaining_points), dtype=bool)
            mask[list(hull_indices)] = False
            remaining_points = remaining_points[mask]
            layer += 1
            
        except QhullError:
            break

    # Scatter plot points
    ax.scatter(points[:, 0], points[:, 1], c='blue', s=50)

    # Annotate order numbers
    for idx, (px, py) in enumerate(points):
        ax.text(px, py, str(idx+1), fontsize=10, ha='right', va='bottom')

    empty_tris, non_empty_tris = get_triangle_lists(points)
    ax.set_title(f"Type #{i} (N={n_points})\\nEmpty Triangles: {len(empty_tris)} | Non-Empty Triangles: {len(non_empty_tris)}")
    ax.axis('off') # Hide axes for cleaner images
    
    if show_triangles_list:
        # Setup text axes for lists
        ax_text.axis('off')
        
        empty_str = "Empty Triangles:\n"
        for idx in range(0, len(empty_tris), 3):
            empty_str += ", ".join(f"({t[0]},{t[1]},{t[2]})" for t in empty_tris[idx:idx+3]) + "\n"
            
        non_empty_str = "Non-Empty Triangles:\n"
        for idx in range(0, len(non_empty_tris), 3):
            non_empty_str += ", ".join(f"({t[0]},{t[1]},{t[2]})" for t in non_empty_tris[idx:idx+3]) + "\n"
            
        # Write two columns of text in the second plot area
        ax_text.text(0.05, 0.95, empty_str, va='top', ha='left', fontsize=8, transform=ax_text.transAxes)
        ax_text.text(0.55, 0.95, non_empty_str, va='top', ha='left', fontsize=8, transform=ax_text.transAxes)
    
    # Save file
    save_name = f"{len(non_empty_tris)}NET_{file_base}_{i:06d}.png"
    save_path = os.path.join(output_dir, save_name)
    
    plt.savefig(save_path, bbox_inches='tight')
    plt.close(fig) # Close memory to prevent RAM leaks
    return i

def save_all_order_types(filepath, max_plots=500, num_processes=None, show_triangles_list=False, iterative_hulls=True):
    """
    Reads an order type file and saves images for every point set found.
    
    Args:
        filepath: Path to .b08 or .b16 file.
        max_plots: Safety limit. Set to None to save ALL (use caution with N >= 8).
        num_processes: Number of CPU cores to use. Set to None for all available cores.
        show_triangles_list: If True, render the list of empty/non-empty triples next to the plot.
        iterative_hulls: If True, recursively draw new convex hulls on points inside the previous hulls.
    """
    filename = os.path.basename(filepath)
    file_base, ext = os.path.splitext(filename)
    
    # 1. Parse N (points per set)
    try:
        # Assumes format "otypes05.b08" -> takes "05"
        n_points = int(filename[6:8])
    except ValueError:
        print(f"[-] Error: Could not figure out N from filename '{filename}'.")
        return

    # 2. Determine bit depth
    if ext == '.b08':
        dtype = np.uint8
    elif ext == '.b16':
        dtype = np.uint16 
    else:
        print(f"[-] Error: Unknown extension {ext}")
        return

    # 3. Read File
    if not os.path.exists(filepath):
        print(f"[-] Error: File {filepath} not found.")
        return

    print(f"[+] Reading {filename}...")
    with open(filepath, 'rb') as f:
        data = np.frombuffer(f.read(), dtype=dtype)

    # 4. Reshape Data
    # Shape: (Number_of_Types, N_Points, 2_Coords)
    try:
        point_sets = data.reshape(-1, n_points, 2)
    except ValueError:
        print("[-] Error: File size does not match point count. File might be corrupted.")
        return

    total_sets = len(point_sets)
    print(f"[+] Found {total_sets} unique order types.")

    # 5. Prepare Output Directory
    output_dir = f"plots_{file_base}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"[+] Saving images to folder: ./{output_dir}/")

    # 6. Loop and Save using multiple cores
    limit = total_sets if max_plots is None else min(total_sets, max_plots)

    if max_plots is not None and total_sets > max_plots:
        print(f"[!] Warning: Only saving the first {max_plots} plots. Set max_plots=None to save all.")

    tasks = [(i, point_sets[i], n_points, file_base, output_dir, show_triangles_list, iterative_hulls) for i in range(limit)]
    count = 0
    with multiprocessing.Pool(processes=num_processes) as pool:
        for _ in pool.imap_unordered(process_point_set, tasks):
            count += 1
            if count % 100 == 0:
                print(f"    ...saved {count}/{limit}")

    print(f"[+] Done. Saved {count} images in '{output_dir}'.")

# ==========================================
# EXECUTION
# ==========================================

# 1. Download 'otypes06.b08' or 'otypes05.b08' into this folder.
# 2. Run the function:

if __name__ == '__main__':
    # Example for 5 points (Only 3 images)
    # save_all_order_types('otypes05.b08')

    # Example for 6 points (16 images)
    # save_all_order_types('otypes06.b08')

    # save_all_order_types('otypes07.b08', max_plots=None)

    # Example for 8 points (3315 images) - Will take a while!
    save_all_order_types('otypes08.b08', max_plots=None, num_processes=None, show_triangles_list=False, iterative_hulls=True)

    # Example for 9 points (158 817 images) - Will take a while!
    # save_all_order_types('otypes09.b16', max_plots=None, num_processes=None)



'''
A note about how the number of order types (possible point configurations) are growing with the number of points:

| Number of Points | Number of sets | File | 08 / 16 Bit | Filesize |
|---|---|---|---|---|
| 3 | 1 | [otypes03.b08](otypes03.b08) | 08 | 6 |
| 4 | 2 | [otypes04.b08](otypes04.b08) | 08 | 16 |
| 5 | 3 | [otypes05.b08](otypes05.b08) | 08 | 30 |
| 6 | 16 | [otypes06.b08](otypes06.b08) | 08 | 192 |
| 7 | 135 | [otypes07.b08](otypes07.b08) | 08 | 1 890 |
| 8 | 3 315 | [otypes08.b08](otypes08.b08) | 08 | 53 040 |
| 9 | 158 817 | [otypes09.b16](otypes09.b16) | 16 | 5 717 412 |
| 10 | 14 309 547 | [otypes10.b16](otypes10.b16) | 16 | 572 381 880 |
| 11 | 2 334 512 907 | --- | 16 | 96 GB |
'''