"""Warehouse drawing, interactive controls and Agg-compatible exports."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle, Rectangle
from matplotlib.widgets import Button, CheckButtons, Slider

from .simulation import Replay
from .validation import metrics, position

COLORS = [
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#56B4E9",
    "#6B4C9A",
    "#7A542E",
]


def draw(ax, s, data, tick, overlays=True):
    ax.clear()
    ax.set_facecolor("#f5f7fa")
    for x, y in s.obstacles:
        ax.add_patch(
            Rectangle(
                (x - 0.47, y - 0.47),
                0.94,
                0.94,
                facecolor="#354052",
                edgecolor="#263143",
            )
        )
    arrivals = 0
    for i, r in enumerate(sorted(s.robots, key=lambda r: r.id)):
        color = COLORS[i % len(COLORS)]
        path = data["paths"][r.id]
        if overlays:
            ax.plot(
                [p[0] for p in path],
                [p[1] for p in path],
                color=color,
                alpha=0.28,
                lw=2,
            )
            trail = path[: min(tick + 1, len(path))]
            ax.plot(
                [p[0] for p in trail],
                [p[1] for p in trail],
                color=color,
                lw=3,
                alpha=0.6,
            )
        ax.add_patch(
            Rectangle(
                (r.start[0] - 0.43, r.start[1] - 0.43),
                0.86,
                0.86,
                fill=False,
                edgecolor=color,
                linestyle="--",
            )
        )
        ax.scatter(
            *r.goal,
            marker="s",
            s=160,
            facecolors="none",
            edgecolors=color,
            linewidths=2,
        )
        ax.text(
            r.goal[0] + 0.18,
            r.goal[1] + 0.25,
            "G" + r.id,
            color=color,
            fontsize=8,
            weight="bold",
        )
        p = position(path, tick)
        ax.add_patch(
            Circle(p, 0.32, facecolor=color, edgecolor="white", lw=1.5, zorder=5)
        )
        ax.text(
            *p,
            r.id,
            color="white",
            ha="center",
            va="center",
            fontsize=8,
            weight="bold",
            zorder=6,
        )
        arrivals += tick >= len(path) - 1
    current = [e for e in data["validation"]["conflicts"] if e["tick"] == tick]
    for e in current:
        for p in e["cells"]:
            ax.scatter(
                *p, s=700, facecolors="none", edgecolors="red", linewidths=3, zorder=8
            )
            ax.annotate(
                f"{e['kind']}: {' + '.join(e['robots'])}",
                p,
                xytext=(12, -28),
                textcoords="offset points",
                color="#bb1d32",
                fontsize=10,
                weight="bold",
                zorder=9,
            )
    m = metrics(data["paths"])
    unsafe = bool(data["validation"]["conflicts"])
    ax.set_title(
        f"{s.name}   {data['algorithm']}   {'UNSAFE' if unsafe else 'VALIDATED SAFE'}\n"
        f"tick {tick}/{m['makespan']}   arrivals {arrivals}/{len(s.robots)}   "
        f"cost {m['sum_cost']}   planning {data['elapsed'] * 1000:.1f} ms",
        fontsize=12,
        color="#bb1d32" if unsafe else "#173d32",
        pad=12,
    )
    ax.set_xlim(-0.7, s.width - 0.3)
    ax.set_ylim(-0.7, s.height - 0.3)
    ax.set_xticks(range(s.width))
    ax.set_yticks(range(s.height))
    ax.grid(alpha=0.15)
    ax.set_aspect("equal")
    ax.set_xlabel(
        "x (east)     dashed = start     square G = destination     dark = shelf"
    )
    ax.set_ylabel("y (north)")


def export(s, data, output, *, tick=0, fps=5):
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 8))
    fig.subplots_adjust(top=0.87, bottom=0.1, left=0.08, right=0.96)
    if target.suffix.lower() == ".gif":
        end = max(len(p) for p in data["paths"].values())
        anim = FuncAnimation(
            fig,
            lambda t: draw(ax, s, data, min(t, end - 1)),
            frames=end + 5,
            interval=1000 / fps,
        )
        anim.save(target, writer=PillowWriter(fps=fps), dpi=95)
    else:
        draw(ax, s, data, tick)
        fig.savefig(target, dpi=160)
    plt.close(fig)


def interactive(s, data):
    replay = Replay(data["paths"])
    fig, ax = plt.subplots(figsize=(12, 9))
    fig.subplots_adjust(bottom=0.22, top=0.88)
    playing = [False]
    overlays = [True]
    draw(ax, s, data, 0)

    def update():
        draw(ax, s, data, replay.tick, overlays[0])
        fig.canvas.draw_idle()

    timer = fig.canvas.new_timer(interval=250)

    def advance():
        if playing[0]:
            replay.step()
            update()
            if replay.tick == replay.makespan:
                playing[0] = False

    timer.add_callback(advance)
    timer.start()
    controls = []
    for label, left, callback in [
        ("Play / pause", 0.13, lambda _: playing.__setitem__(0, not playing[0])),
        ("Step", 0.33, lambda _: (replay.step(), update())),
        (
            "Reset",
            0.47,
            lambda _: (playing.__setitem__(0, False), replay.reset(), update()),
        ),
    ]:
        b = Button(fig.add_axes([left, 0.1, 0.13, 0.045]), label)
        b.on_clicked(callback)
        controls.append(b)
    slider = Slider(
        fig.add_axes([0.2, 0.045, 0.4, 0.025]), "ticks/sec", 1, 12, valinit=4
    )
    slider.on_changed(lambda v: setattr(timer, "interval", int(1000 / v)))
    check = CheckButtons(
        fig.add_axes([0.68, 0.05, 0.18, 0.10]), ["paths and trails"], [True]
    )
    check.on_clicked(lambda _: (overlays.__setitem__(0, not overlays[0]), update()))
    # Keep controls and timer alive until the window closes.
    fig._warehouse_controls = (controls, slider, check, timer)
    plt.show()
