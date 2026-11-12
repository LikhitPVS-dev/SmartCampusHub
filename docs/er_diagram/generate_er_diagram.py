"""
database/generate_er_diagram.py
Person 1 – Database Foundation | SmartCampusHub

Generates ER_Diagram.png using matplotlib.
Run:  python database/generate_er_diagram.py
Requires: pip install matplotlib
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

# ── Color palette ─────────────────────────────────────────────────────────────
CLR_HEADER   = "#1a73e8"      # table header background
CLR_PK       = "#fce8b2"      # PK row background
CLR_FK       = "#e8f5e9"      # FK row background
CLR_NORMAL   = "#ffffff"      # normal row background
CLR_BORDER   = "#444444"      # table border / text
CLR_HEADER_T = "#ffffff"      # header text
CLR_ARROW    = "#c0392b"      # relationship arrow colour

FONT_HEADER  = dict(fontsize=8.5, fontweight="bold", color=CLR_HEADER_T, va="center", ha="center")
FONT_FIELD   = dict(fontsize=7,   color=CLR_BORDER,  va="center", ha="left")
FONT_TYPE    = dict(fontsize=6.5, color="#555555",   va="center", ha="right")

ROW_H  = 0.30   # height of each column row
HDR_H  = 0.40   # height of table header row
PAD    = 0.08   # horizontal padding inside cell
COL_W  = 2.80   # total table width


def draw_table(ax, x, y, name: str, columns: list[tuple[str, str, str]]) -> dict:
    """
    Draw one table box.

    Parameters
    ----------
    ax      : matplotlib Axes
    x, y    : bottom-left corner (data coordinates)
    name    : table name
    columns : list of (col_name, pg_type, flag)
              flag: "PK" | "FK" | "PK,FK" | ""

    Returns
    -------
    dict  with anchor points:
        "top_mid", "bot_mid", "right_mid", "left_mid"
        and per-column "right_{col}" / "left_{col}" for FK arrows
    """
    nrows   = len(columns)
    total_h = HDR_H + nrows * ROW_H

    # --- header ---
    rect = mpatches.FancyBboxPatch(
        (x, y + nrows * ROW_H), COL_W, HDR_H,
        boxstyle="square,pad=0", linewidth=1,
        edgecolor=CLR_BORDER, facecolor=CLR_HEADER
    )
    ax.add_patch(rect)
    ax.text(x + COL_W / 2, y + nrows * ROW_H + HDR_H / 2,
            name, **FONT_HEADER)

    # --- column rows ---
    for i, (cname, ctype, flag) in enumerate(reversed(columns)):
        row_y = y + i * ROW_H
        bg = CLR_PK if "PK" in flag else (CLR_FK if "FK" in flag else CLR_NORMAL)
        rect = mpatches.FancyBboxPatch(
            (x, row_y), COL_W, ROW_H,
            boxstyle="square,pad=0", linewidth=0.6,
            edgecolor="#aaaaaa", facecolor=bg
        )
        ax.add_patch(rect)

        prefix = ""
        if flag == "PK":       prefix = "[PK] "
        elif flag == "FK":     prefix = "[FK] "
        elif flag == "PK,FK":  prefix = "[PK+FK] "

        ax.text(x + PAD, row_y + ROW_H / 2,
                f"{prefix}{cname}", **FONT_FIELD)
        ax.text(x + COL_W - PAD, row_y + ROW_H / 2,
                ctype, **FONT_TYPE)

    # outer border
    border = mpatches.FancyBboxPatch(
        (x, y), COL_W, total_h,
        boxstyle="square,pad=0", linewidth=1.5,
        edgecolor=CLR_BORDER, facecolor="none"
    )
    ax.add_patch(border)

    # anchor points
    cx = x + COL_W / 2
    cy = y + total_h / 2
    return {
        "top_mid":   (cx, y + total_h),
        "bot_mid":   (cx, y),
        "left_mid":  (x,  cy),
        "right_mid": (x + COL_W, cy),
        "left_top":  (x,  y + total_h),
        "right_top": (x + COL_W, y + total_h),
        # per-column anchors (row 0 = bottom-most column in `columns` list)
        **{
            f"left_{c[0]}":  (x,          y + (len(columns)-1-i)*ROW_H + ROW_H/2)
            for i, c in enumerate(columns)
        },
        **{
            f"right_{c[0]}": (x+COL_W,    y + (len(columns)-1-i)*ROW_H + ROW_H/2)
            for i, c in enumerate(columns)
        },
    }


def arrow(ax, start, end, label="", offset_start=(0,0), offset_end=(0,0)):
    sx, sy = start[0]+offset_start[0], start[1]+offset_start[1]
    ex, ey = end[0]+offset_end[0],     end[1]+offset_end[1]
    ax.annotate(
        "", xy=(ex, ey), xytext=(sx, sy),
        arrowprops=dict(
            arrowstyle="-|>",
            color=CLR_ARROW,
            lw=1.2,
            connectionstyle="arc3,rad=0.0",
        )
    )
    if label:
        mx, my = (sx+ex)/2, (sy+ey)/2
        ax.text(mx+0.05, my+0.05, label, fontsize=5.5,
                color=CLR_ARROW, ha="center", va="bottom",
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=1))


# ── Table definitions (col_name, pg_type, flag) ───────────────────────────────

USERS = [
    ("user_id",       "INTEGER",      "PK"),
    ("full_name",     "VARCHAR(150)", ""),
    ("email",         "VARCHAR(255)", ""),
    ("password_hash", "TEXT",         ""),
    ("role",          "VARCHAR(20)",  ""),
    ("department",    "VARCHAR(100)", ""),
]

EVENTS = [
    ("event_id",              "INTEGER",     "PK"),
    ("title",                 "VARCHAR(200)",""),
    ("description",           "TEXT",        ""),
    ("event_type",            "VARCHAR(50)", ""),
    ("start_date",            "TIMESTAMPTZ", ""),
    ("end_date",              "TIMESTAMPTZ", ""),
    ("registration_deadline", "TIMESTAMPTZ", ""),
    ("venue",                 "VARCHAR(255)",""),
    ("organizer_id",          "INTEGER",     "FK"),
    ("status",                "VARCHAR(20)", ""),
    ("max_participants",      "INTEGER",     ""),
]

REGISTRATIONS = [
    ("registration_id",   "INTEGER",     "PK"),
    ("student_id",        "INTEGER",     "FK"),
    ("event_id",          "INTEGER",     "FK"),
    ("registration_date", "TIMESTAMPTZ", ""),
    ("status",            "VARCHAR(20)", ""),
]

ANNOUNCEMENTS = [
    ("announcement_id", "INTEGER",     "PK"),
    ("title",           "VARCHAR(200)",""),
    ("content",         "TEXT",        ""),
    ("published_at",    "TIMESTAMPTZ", ""),
    ("created_by",      "INTEGER",     "FK"),
    ("event_id",        "INTEGER",     "FK"),
]

HACKATHON_TEAMS = [
    ("team_id",        "INTEGER",     "PK"),
    ("team_name",      "VARCHAR(100)",""),
    ("hackathon_id",   "INTEGER",     "FK"),
    ("team_leader_id", "INTEGER",     "FK"),
]

TEAM_MEMBERS = [
    ("team_id",    "INTEGER", "PK,FK"),
    ("student_id", "INTEGER", "PK,FK"),
]


def main():
    fig, ax = plt.subplots(figsize=(22, 14))
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 14)
    ax.axis("off")
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("#f8f9fa")

    ax.text(11, 13.5, "SmartCampusHub – College Portal ER Diagram",
            fontsize=14, fontweight="bold", ha="center", va="center", color="#1a1a1a")
    ax.text(11, 13.1, "Person 1 – Database Foundation",
            fontsize=9, ha="center", va="center", color="#555555")

    # ── Table positions (x, y = bottom-left) ─────────────────────────────────
    # Layout:
    #    users (center-top)
    #    events (center-mid)   registrations (right-mid)
    #    announcements (left)  hackathon_teams (center-bot)  team_members (right-bot)

    u  = draw_table(ax,  8.5, 9.0,  "users",           USERS)
    e  = draw_table(ax,  8.5, 4.5,  "events",          EVENTS)
    r  = draw_table(ax, 14.0, 5.5,  "registrations",   REGISTRATIONS)
    an = draw_table(ax,  2.0, 5.0,  "announcements",   ANNOUNCEMENTS)
    ht = draw_table(ax,  8.5, 0.5,  "hackathon_teams", HACKATHON_TEAMS)
    tm = draw_table(ax, 14.0, 0.5,  "team_members",    TEAM_MEMBERS)

    # ── Relationships (FK → PK arrows) ───────────────────────────────────────

    # events.organizer_id → users.user_id
    arrow(ax, e["right_organizer_id"], u["bot_mid"],
          label="1:N organizer_id")

    # registrations.student_id → users.user_id
    arrow(ax, r["left_student_id"], u["right_mid"],
          label="1:N student_id")

    # registrations.event_id → events.event_id
    arrow(ax, r["left_event_id"], e["right_mid"],
          label="1:N event_id")

    # announcements.created_by → users.user_id
    arrow(ax, an["right_created_by"], u["left_mid"],
          label="1:N created_by")

    # announcements.event_id → events.event_id
    arrow(ax, an["right_event_id"], e["left_mid"],
          label="1:N (nullable)")

    # hackathon_teams.hackathon_id → events.event_id
    arrow(ax, ht["top_mid"], e["bot_mid"],
          label="1:N hackathon_id")

    # hackathon_teams.team_leader_id → users.user_id
    arrow(ax, ht["right_team_leader_id"], u["bot_mid"],
          label="1:N team_leader_id", offset_end=(0.2, 0))

    # team_members.team_id → hackathon_teams.team_id
    arrow(ax, tm["left_team_id"], ht["right_team_id"],
          label="1:N team_id")

    # team_members.student_id → users.user_id
    arrow(ax, tm["right_student_id"], u["right_mid"],
          label="1:N member", offset_start=(0, -0.1), offset_end=(0, -0.4))

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_x, legend_y = 0.3, 2.0
    for bg, lbl in [(CLR_PK, "Primary Key"), (CLR_FK, "Foreign Key"),
                    (CLR_NORMAL, "Regular column")]:
        patch = mpatches.Patch(facecolor=bg, edgecolor="#aaaaaa", label=lbl)
        ax.add_patch(mpatches.FancyBboxPatch(
            (legend_x, legend_y), 0.4, 0.22,
            boxstyle="square,pad=0", facecolor=bg, edgecolor="#aaaaaa", lw=0.6
        ))
        ax.text(legend_x + 0.5, legend_y + 0.11, lbl,
                fontsize=7, va="center", color=CLR_BORDER)
        legend_y -= 0.32

    ax.text(0.3, legend_y, "[PK] Primary Key  [FK] Foreign Key  -> one-to-many FK reference",
            fontsize=6.5, color="#666666", va="center")

    out_path = os.path.join(os.path.dirname(__file__), "ER_Diagram.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight")
    print(f"ER diagram saved to: {out_path}")


if __name__ == "__main__":
    main()
