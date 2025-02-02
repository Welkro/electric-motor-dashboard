import pandas as pd
import numpy as np 
import lightningchart as lc

# Add license key
lc.set_license('LICENSE_KEY')

# Load dataset
dataset = 'dataset/measures_v2.csv'
df = pd.read_csv(dataset)

# Initialize the dashboard
dashboard = lc.Dashboard(columns=3, rows=3, theme=lc.Themes.Dark)


# LINE CHART: TEMPERATURE TRENDS
chart_line = dashboard.ChartXY(column_index=0, row_index=0, column_span=2)
chart_line.set_title("Average Temperature Over Profiles")

# Group by profile_id and compute mean temperature values
df_avg_temp = df.groupby("profile_id")[["coolant", "stator_winding", "stator_tooth", "stator_yoke", "pm", "ambient"]].mean().reset_index()

# X-axis: Profile ID
x_values = df_avg_temp["profile_id"].tolist()

# Add each temperature series dynamically
for col in ["coolant", "stator_winding", "stator_tooth", "stator_yoke", "pm", "ambient"]:
    y_values = df_avg_temp[col].tolist()
    series = chart_line.add_line_series(data_pattern='ProgressiveX')
    series.append_samples(x_values, y_values).set_name(col)

# Set axis labels
chart_line.get_default_x_axis().set_title("Profile ID")
chart_line.get_default_y_axis().set_title("Average Temperature (°C)")

# Add legend
legend = chart_line.add_legend()
legend.add(chart_line)

# HISTOGRAM: STATOR WINDING TEMPERATURE DISTRIBUTION
chart_histogram = dashboard.BarChart(column_index=2, row_index=0, column_span=1, row_span=3)
chart_histogram.set_title("Stator Winding Temp")
chart_histogram.set_sorting("disabled")

# Extract temperature data
temperature_values = df["stator_winding"].dropna().to_numpy()

# Define bins for the histogram
num_bins = 25
counts, bin_edges = np.histogram(temperature_values, bins=num_bins)

# Prepare histogram data
bar_data = [
    {"category": f"{bin_edges[i]:.1f}–{bin_edges[i+1]:.1f}", "value": int(count)}
    for i, count in enumerate(counts)
]
# Set the histogram data
chart_histogram.set_data(bar_data)

# Disable sorting to maintain order
chart_histogram.set_sorting("disabled")

# Get min and max temperature for normalization
min_temp = min(temperature_values)
max_temp = max(temperature_values)

# Define a smooth gradient from blue (cold) to red (hot)
def get_color(value, min_val, max_val):
    """ Returns a color interpolated from blue to red based on value. """
    ratio = (value - min_val) / (max_val - min_val)  # Normalize to [0,1]
    
    # Interpolated RGB colors (Blue -> Cyan -> Green -> Yellow -> Red)
    if ratio < 0.25:
        return lc.Color(0, int(255 * (ratio / 0.25)), 255)  # Blue to Cyan
    elif ratio < 0.50:
        return lc.Color(0, 255, int(255 * (1 - (ratio - 0.25) / 0.25)))  # Cyan to Green
    elif ratio < 0.75:
        return lc.Color(int(255 * ((ratio - 0.50) / 0.25)), 255, 0)  # Green to Yellow
    else:
        return lc.Color(255, int(255 * (1 - (ratio - 0.75) / 0.25)), 0)  # Yellow to Red

# Apply the colors manually using set_bar_color() method 
for i, bar in enumerate(bar_data):
    bin_center = (bin_edges[i] + bin_edges[i+1]) / 2  # Get the bin's center temperature
    color = get_color(bin_center, min_temp, max_temp)
    chart_histogram.set_bar_color(bar["category"], color)

# SCATTER PLOT: TORQUE VS MOTOR SPEED
chart_scatter = dashboard.ChartXY(column_index=0, row_index=1, column_span=2)
chart_scatter.set_title("Torque vs. Motor Speed")
chart_scatter.get_default_x_axis().set_title("Motor Speed (rpm)")
chart_scatter.get_default_y_axis().set_title("Torque (Nm)")

x_values = df["motor_speed"]
y_values = df["torque"]


point_series = chart_scatter.add_point_series(data_pattern='ProgressiveY')

point_series.set_palette_point_coloring(
    steps=[
        {"value": y_values.min(), "color": lc.Color("blue")},
        {"value": y_values.quantile(0.25), "color": lc.Color("cyan")},
        {"value": y_values.median(), "color": lc.Color("yellow")},
        {"value": y_values.quantile(0.75), "color": lc.Color("orange")},
        {"value": y_values.max(), "color": lc.Color("red")},
    ],
    look_up_property="y",
    percentage_values=False
)
point_series.add(x=x_values, y=y_values)

# AVERAGE TEMPERATURE HEATMAP 
chart_heatmap = dashboard.ChartXY(column_index=0, row_index=2, column_span=2)
chart_heatmap.set_title("Avg Stator Winding Temp Across Speed & Torque")


# Define bin size for motor speed and torque
num_bins_speed = 500  # Adjust for resolution
num_bins_torque = 500

# Create bins for motor speed and torque
df['speed_bin'] = pd.cut(df['motor_speed'], bins=num_bins_speed, labels=False)
df['torque_bin'] = pd.cut(df['torque'], bins=num_bins_torque, labels=False)

# Compute average stator winding temperature for each bin
heatmap_data = df.groupby(['speed_bin', 'torque_bin'])['stator_winding'].mean().unstack()

# Convert NaN values to zero
heatmap_data = heatmap_data.fillna(0)

# Convert to numpy array for heatmap
heatmap_array = heatmap_data.to_numpy()

# Define grid size
grid_size_x, grid_size_y = heatmap_array.shape

# Create heatmap series
heatmap_series = chart_heatmap.add_heatmap_grid_series(
    columns=grid_size_x,
    rows=grid_size_y,
)

# Set heatmap grid positions
heatmap_series.set_start(x=0, y=0)
heatmap_series.set_end(x=grid_size_x, y=grid_size_y)
heatmap_series.set_step(x=1, y=1)
heatmap_series.set_intensity_interpolation(True)

# Assign the computed values
heatmap_series.invalidate_intensity_values(heatmap_array.tolist())

# Hide wireframe for a cleaner look
heatmap_series.hide_wireframe()

# Define color gradient from cool to hot temperatures
custom_palette = [
    {"value": np.nanmin(heatmap_array), "color": lc.Color("blue")},   # Low temperature (Blue)
    {"value": np.nanpercentile(heatmap_array, 25), "color": lc.Color("cyan")},
    {"value": np.nanmedian(heatmap_array), "color": lc.Color("yellow")},
    {"value": np.nanpercentile(heatmap_array, 75), "color": lc.Color("orange")},
    {"value": np.nanmax(heatmap_array), "color": lc.Color("red")}    # High temperature (Red)
]

# Apply color palette to the heatmap
heatmap_series.set_palette_coloring(
    steps=custom_palette,
    look_up_property="value",
    interpolate=True
)

# Set axis titles
chart_heatmap.get_default_x_axis().set_title("Motor Speed Bins")
chart_heatmap.get_default_y_axis().set_title("Torque Bins")

# Add a legend
chart_heatmap.add_legend(data=heatmap_series, horizontal=True).set_title("Avg Stator Winding Temp (°C)")

# OPEN DASHBOARD 
dashboard.open()
