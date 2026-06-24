def filter(ins, outs):
    import numpy as np
    from collections import defaultdict

    x = ins['X']
    y = ins['Y']
    z = ins['Z']
    gps_time = ins['GpsTime']
    return_num = ins['ReturnNumber']
    # num_returns = ins['NumberOfReturns']

    num_points = len(x)
    gap_to_next = np.zeros(num_points)

    # Group indices by GpsTime
    pulse_map = defaultdict(list)
    for i in range(num_points):
        pulse_map[gps_time[i]].append(i)

    # Debug:
    # with open(file = "defaultdict.txt", mode="w") as f:
    #     f.write(str(pulse_map))

    for indices in pulse_map.values():
        if len(indices) < 2:
            continue  # Skip single-return pulses
        # Sort by ReturnNumber
        sorted_indices = sorted(indices, key=lambda i: return_num[i])

        for i in range(len(sorted_indices) - 1):
            idx_current = sorted_indices[i]
            idx_next = sorted_indices[i + 1]

            dx = x[idx_next] - x[idx_current]
            dy = y[idx_next] - y[idx_current]
            dz = z[idx_next] - z[idx_current]
            gap_to_next[idx_current] = (dx**2 + dy**2 + dz**2)**0.5

        # Last return has no next return
        gap_to_next[sorted_indices[-1]] = 0.0

    outs['gapToNextReturn'] = np.asanyarray(gap_to_next.tolist())

    return True
