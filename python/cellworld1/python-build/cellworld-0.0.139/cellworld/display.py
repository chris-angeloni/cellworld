import numpy
from matplotlib.patches import RegularPolygon
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib.path import Path
from matplotlib.transforms import Affine2D
import matplotlib.colors as mcolors
from .world import *
from .experiment import *
from .agent_markers import *
from .QuickBundles import *


def adjust_color_brightness(color, amount:float=1):
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])


class Display:

    def __init__(self,
                 world: World,
                 fig_size: tuple = (10, 10),
                 padding: float = .1,
                 outline: float = .5,
                 show_axes: bool = False,
                 cell_color="white",
                 occlusion_color="black",
                 background_color="white",
                 habitat_color="white",
                 cell_edge_color="lightgray",
                 habitat_edge_color="gray",
                 animated: bool = False,
                 ax=None,
                 fig=None):
        if animated:
            plt.ion()
        self.agents = dict()
        self.agents_markers = dict()
        self.agents_markers["predator"] = Agent_markers.robot()
        self.agents_markers["prey"] = Agent_markers.mouse()
        self.animated = animated
        self.world = world
        if not fig:
            self.fig = plt.figure(figsize=fig_size)
        else:
            self.fig = fig
        if not ax:
            self.ax = self.fig.add_subplot(111)
        else:
            self.ax = ax
        self.ax.axes.xaxis.set_visible(show_axes)
        self.ax.axes.yaxis.set_visible(show_axes)
        self.agents_trajectories = Trajectories()
        self.agents_markers = dict()
        self.cells = []
        self.occlusion_color = occlusion_color
        self.habitat_color = habitat_color
        self.habitat_edge_color = habitat_edge_color
        self.cell_color = cell_color
        self.cell_edge_color = cell_edge_color
        self.xcenter = world.implementation.space.center.x
        self.ycenter = world.implementation.space.center.y
        self.outline = outline
        hsize = world.implementation.space.transformation.size / 2
        pad = hsize * padding

        xmin = self.xcenter - hsize - pad
        xmax = self.xcenter + hsize + pad

        ymin = self.ycenter - hsize - pad
        ymax = self.ycenter + hsize + pad

        self.ax.set_xlim(xmin=xmin, xmax=xmax)
        self.ax.set_ylim(ymin=ymin, ymax=ymax)
        self.ax.set_facecolor(background_color)
        self.habitat_theta = math.radians(0 - world.implementation.space.transformation.rotation)
        self.cells_theta = math.radians(0 - world.implementation.cell_transformation.rotation) + self.habitat_theta
        self.cells_size = world.implementation.cell_transformation.size / 2
        self.habitat_size = hsize
        self.cell_polygons = []
        self.cell_outline_polygons = []
        self.habitat_polygon = None
        self._draw_cells__()
        plt.tight_layout()

    def _draw_cells__(self):
        [p.remove() for p in reversed(self.ax.patches)]
        for cell in self.world.cells:
            color = self.occlusion_color if cell.occluded else self.cell_color
            self.cell_outline_polygons.append(self.ax.add_patch(RegularPolygon((cell.location.x, cell.location.y), self.world.configuration.cell_shape.sides, self.cells_size, facecolor=color, edgecolor=self.cell_edge_color, orientation=self.cells_theta, zorder=-3, linewidth=1)))
            self.cell_polygons.append(self.ax.add_patch(RegularPolygon((cell.location.x, cell.location.y), self.world.configuration.cell_shape.sides, self.cells_size * self.outline, facecolor=color, orientation=self.cells_theta, zorder=-2, linewidth=1)))
        self.habitat_polygon = self.ax.add_patch(RegularPolygon((self.xcenter, self.ycenter), self.world.implementation.space.shape.sides, self.habitat_size, facecolor=self.habitat_color, edgecolor=(1,1,1,0), orientation=self.habitat_theta, zorder=-4))
        self.habitat_polygon_edge = self.ax.add_patch(RegularPolygon((self.xcenter, self.ycenter), self.world.implementation.space.shape.sides, self.habitat_size, facecolor=(1,1,1,0), edgecolor=self.habitat_edge_color, orientation=self.habitat_theta, zorder=-1))

    def set_occlusions(self, occlusions: Cell_group_builder):
        self.world.set_occlusions(occlusions)
        self._draw_cells__()

    def set_agent_marker(self, agent_name: str, marker: Path):
        self.agents_markers[agent_name] = marker

    def add_trajectories(self, trajectories: Trajectories, colors={}, alphas={}):
        agents = trajectories.get_agent_names()
        for index, agent in enumerate(agents):
            locations = trajectories.get_agent_trajectory(agent).get("location")
            x = locations.get("x")
            y = locations.get("y")
            color = list(matplotlib.colors.cnames.keys())[index]
            alpha = 0.5
            if agent in colors:
                color = colors[agent]
            if agent in alphas:
                alpha = alphas[agent]
            for i in range(len(x)-1):
                lcolor = None
                lalpha = None
                if type(alpha) is list:
                    lalpha = alpha[i]
                else:
                    lalpha = alpha
                if type(color) is numpy.ndarray:
                    lcolor = color[i]
                else:
                    lcolor = color
                self.ax.plot([x[i], x[i+1]], [y[i], y[i+1]], color=lcolor, alpha=lalpha, linewidth=3)


    def cell(self, cell: Cell = None, cell_id: int = -1, coordinates: Coordinates = None, color=None, outline_color=None, edge_color=None):
        if color is None:
            color = self.cell_color
        if edge_color is None:
            edge_color = self.cell_edge_color
        if cell is None:
            if cell_id == -1:
                if coordinates is None:
                    raise RuntimeError("a cell, cell_id or coordinates must be provided")
                for c in self.world.cells:
                    if c.coordinates == coordinates:
                        cell = c
                        break
                if cell is None:
                    raise RuntimeError("cell coordinates not found")
            else:
                cell = self.world.cells[cell_id]
        if outline_color is None:
            outline_color = color
        self.cell_polygons[cell.id].set_facecolor(color)
        self.cell_outline_polygons[cell.id].set_edgecolor(edge_color)
        self.cell_outline_polygons[cell.id].set_facecolor(outline_color)

    def heatmap(self, values: list, color_map=plt.cm.Reds, value_range: tuple = None) -> None:
        if value_range:
            minv, maxv = value_range
        else:
            minv, maxv = min(values), max(values)

        if (minv == maxv):
            return
        adjusted_values = [(v-minv)/(maxv-minv) for v in values]
        adjusted_cmap = color_map(adjusted_values)
        for cell_id, color in enumerate(adjusted_cmap):
            if not self.world.cells[cell_id].occluded:
                self.cell(cell_id=cell_id, color=color)

    def circle(self, location: Location, radius: float, color, alpha: float = 1.0, zorder=None):
        circle_patch = plt.Circle((location.x, location.y), radius, color=color, alpha=alpha, zorder=zorder)
        return self.ax.add_patch(circle_patch)

    def arrow(self, beginning: Location, ending: Location = None, theta: float = 0, dist: float = 0, color="black", head_width: float = .02, alpha: float = 1.0, line_width: float = 0.001, existing_arrow: matplotlib.patches.FancyArrowPatch = None) -> matplotlib.patches.FancyArrowPatch:
        if ending is None:
            ending = beginning.copy().move(theta=theta, dist=dist)
        length = ending - beginning
        if existing_arrow:
            existing_arrow.set_data(x=beginning.x, y=beginning.y, dx=length.x, dy=length.y, head_width=head_width, width=line_width)
            existing_arrow.set_color(color)
            existing_arrow.set_alpha(alpha)
            return existing_arrow
        else:
            new_arrow = self.ax.arrow(beginning.x, beginning.y, length.x, length.y, color=color, head_width=head_width, length_includes_head=True, alpha=alpha, width=line_width)
            new_arrow.animated = self.animated
            return new_arrow

    def line(self, beginning: Location, ending: Location = None, theta: float = 0, dist: float = 0, color="black", alpha: float = 1.0, line_width: float = 0.001, existing_line: matplotlib.patches.FancyArrowPatch = None) -> matplotlib.patches.FancyArrowPatch:
        head_width = 0
        if ending is None:
            ending = beginning.copy().move(theta=theta, dist=dist)
        length = ending - beginning
        if existing_line:
            existing_line.set_data(x=beginning.x, y=beginning.y, dx=length.x, dy=length.y, head_width=0, head_length=0, alpha=alpha, width=line_width)
            existing_line.set_color(color)
            existing_line.set_alpha(alpha)
            return existing_line
        else:
            new_arrow = self.ax.arrow(beginning.x, beginning.y, length.x, length.y, color=color, head_width=0, alpha=alpha, head_length=0, length_includes_head=False, width=line_width)
            new_arrow.animated = self.animated
            return new_arrow

    def agent(self, step: Step = None, agent_name: str = None, location: Location = None, rotation: float = None, color=None, size: float = 40.0, show_trajectory: bool = True, marker: Path=None):
        if step:
            agent_name = step.agent_name
            location = step.location
            rotation = step.rotation

        # if show_trajectory:
        #     self.agents_trajectories.append(step)
        #     x = self.agents_trajectories.get_agent_trajectory(agent_name).get("location").get("x")
        #     y = self.agents_trajectories.get_agent_trajectory(agent_name).get("location").get("y")
        #     self.agents[agent_name], = self.ax.plot(x, y, c=color)

        if not marker:
            if agent_name in self.agents_markers:
                marker = self.agents_markers[agent_name]
            else:
                if agent_name == "predator":
                    marker = Agent_markers.robot()
                else:
                    marker = Agent_markers.mouse()

        if agent_name not in self.agents:
            self.agents[agent_name], = self.ax.plot(location.x, location.y, marker=marker, c=color, markersize=size)

        t = Affine2D().rotate_deg_around(0, 0, -rotation)
        self.agents[agent_name].set_marker(marker.transformed(t))
        self.agents[agent_name].set_xdata(location.x)
        self.agents[agent_name].set_ydata(location.y)
        self.agents[agent_name].set_color(color)

    def plot_clusters(self, clusters, colors: list=["blue", "red"], show_centroids: bool = True, use_alpha: bool = True):
        for sl in clusters.unclustered:
            self.ax.plot([s.x for s in sl], [s.y for s in sl], c="gray", linewidth=2, alpha=.5)

        for cn, cluster in enumerate(clusters):
            distances = cluster.get_distances()
            max_distance = max(distances)
            if use_alpha:
                alpha_values = [1 if max_distance == 0 else (max_distance - d) / max_distance / 2 for d in distances]
            else:
                alpha_values = [1 for d in distances]
            color = adjust_color_brightness(colors[cn % len(colors)], .8)
            for i, sl in enumerate(cluster):
                self.ax.plot([s.x for s in sl], [s.y for s in sl], c=color, linewidth=2, alpha=alpha_values[i])

        if show_centroids:
            for cn, cluster in enumerate(clusters):
                color = adjust_color_brightness(colors[cn % len(colors)], 1.2)
                cluster_size = .005 + .01 * (len(cluster) / clusters.streamline_count())
                for s in cluster.centroid:
                    self.circle(s, radius=cluster_size + .003, color="lightgray", alpha=1, zorder=500)
                for s in cluster.centroid:
                    self.circle(s, radius=cluster_size, color=color, alpha=1, zorder=500)


    def update(self):
        if self.animated:
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            plt.pause(.001)
