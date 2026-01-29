import matplotlib
# Set backend to 'Agg' to prevent windows from popping up (Headless mode)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import numpy as np
import os
from scipy.spatial import ConvexHull, QhullError

def save_all_order_types(filepath, max_plots=500):
    """
    Reads an order type file and saves images for every point set found.
    
    Args:
        filepath: Path to .b08 or .b16 file.
        max_plots: Safety limit. Set to None to save ALL (use caution with N >= 8).
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

    # 6. Loop and Save
    count = 0
    limit = total_sets if max_plots is None else min(total_sets, max_plots)

    if max_plots is not None and total_sets > max_plots:
        print(f"[!] Warning: Only saving the first {max_plots} plots. Set max_plots=None to save all.")

    for i in range(limit):
        points = point_sets[i]
        
        # Create Figure (don't show it)
        fig, ax = plt.subplots(figsize=(5, 5))
        
        # Draw Convex Hull (Visual aid to recognize the shape)
        # Wrap in try/except because collinear points might confuse QuickHull
        try:
            if n_points >= 3:
                hull = ConvexHull(points)
                for simplex in hull.simplices:
                    ax.plot(points[simplex, 0], points[simplex, 1], 'k-', alpha=0.3)
        except QhullError:
            pass # Just skip hull if points are collinear or weird

        # Scatter plot points
        ax.scatter(points[:, 0], points[:, 1], c='blue', s=50)

        # Annotate order numbers
        for idx, (px, py) in enumerate(points):
            ax.text(px, py, str(idx+1), fontsize=10, ha='right', va='bottom')

        ax.set_title(f"Type #{i} (N={n_points})")
        ax.axis('off') # Hide axes for cleaner images
        
        # Save file
        save_name = f"{file_base}_{i:06d}.png"
        save_path = os.path.join(output_dir, save_name)
        
        plt.savefig(save_path, bbox_inches='tight')
        plt.close(fig) # Close memory to prevent RAM leaks
        
        count += 1
        if count % 100 == 0:
            print(f"    ...saved {count}/{limit}")

    print(f"[+] Done. Saved {count} images in '{output_dir}'.")

# ==========================================
# EXECUTION
# ==========================================

# 1. Download 'otypes06.b08' or 'otypes05.b08' into this folder.
# 2. Run the function:

# Example for 5 points (Only 3 images)
save_all_order_types('otypes05.b08') 

# Example for 6 points (16 images)
save_all_order_types('otypes06.b08')

save_all_order_types('otypes07.b08', max_plots=None)

# Example for 8 points (3315 images) - Will take a while!
save_all_order_types('otypes08.b08', max_plots=None)
