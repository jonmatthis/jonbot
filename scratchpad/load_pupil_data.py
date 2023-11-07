import pandas as pd

pupil_path = r"C:\Users\jonma\Downloads\pupil_positions.csv"

pupil_df = pd.read_csv(pupil_path)

two_d_method_name = "2d c++"
three_d_method_name = "pye3d 0.3.0 post-hoc"

# extract only the rows that use the 2d method
pupil_df = pupil_df[pupil_df["method"] == three_d_method_name]

# extract only the rows where `eye_id` = 0 and call it "right_eye_df"
right_eye_df = pupil_df[pupil_df["eye_id"] == 0]

# extract only the rows where `eye_id` = 1 and call it "left_eye_df"
left_eye_df = pupil_df[pupil_df["eye_id"] == 1]

# save them both as csv's
right_eye_save_path = r"C:\Users\jonma\Downloads\pupil_positions_right_eye.csv"
left_eye_save_path = r"C:\Users\jonma\Downloads\pupil_positions_left_eye.csv"

right_eye_df.to_csv(right_eye_save_path, index=False)
left_eye_df.to_csv(left_eye_save_path, index=False)

# plot the timeseries in plotly - with right norm_pos_x on the top subplot and right_norm_pos_y on the bottom subplot
import plotly.express as px

fig = px.line(right_eye_df, y="phi", title="Right Eye Phi", markers=True)
fig.show()
f = 9
