from .location import Location, Location_list
from .experiment import Trajectories
from json_cpp import JsonObject, JsonList


def get_ratios(a: float, b: float, v: float) -> tuple:
    r = b - a
    ra = (v - a) / r
    rb = (b - v) / r
    return ra, rb


class StreamLine(Location_list):
    class StreamLineType:
        Distance = 0
        Time = 1

    def __init__(self, trajectory: Trajectories = None, streamline_len: int = 100, streamline_type=StreamLineType.Distance, fixed_interval=(-1, -1)):
        Location_list.__init__(self, allow_empty=True)
        self.closest_steps = JsonList(list_type=int)
        self.interval = 0

        if trajectory is None:
            return

        if streamline_type == StreamLine.StreamLineType.Distance:
            last_step_location = trajectory[0].location
            total_dist = 0
            distances = []
            for step in trajectory:
                total_dist += last_step_location.dist(step.location)
                distances.append(total_dist)
                last_step_location = step.location
            streamline_step_dist = total_dist / streamline_len
            self.interval = streamline_step_dist

            interval_start = 0
            interval_end = total_dist
            if fixed_interval[0] >= 0:
                interval_start = fixed_interval[0]
                interval_end = fixed_interval[1]

            streamline_step_dist = (interval_end - interval_start) / streamline_len
            step_index = 0
            for i in range(streamline_len + 1):
                streamline_step_total_dist = interval_start + i * streamline_step_dist
                while step_index < len(trajectory) and distances[step_index] < streamline_step_total_dist:
                    step_index += 1
                    if step_index == len(trajectory):
                        break
                if step_index == len(trajectory):
                    self.append(None)
                else:
                    if step_index > 0:
                        prev_ratio, next_ratio = get_ratios(distances[step_index - 1], distances[step_index], streamline_step_total_dist)
                        next_streamline_step = trajectory[step_index-1].location * prev_ratio + trajectory[step_index].location * next_ratio
                    else:
                        next_streamline_step = trajectory[step_index].location
                    self.append(next_streamline_step)
                    self.closest_steps.append(step_index)

        else:
            total_time = trajectory[-1].time_stamp - trajectory[0].time_stamp

            interval_start = trajectory[0].time_stamp
            interval_end = total_time
            if fixed_interval[0] >= 0:
                interval_start = fixed_interval[0]
                interval_end = fixed_interval[1]

            streamline_step_time = (interval_end - interval_start) / streamline_len
            step_index = 0
            for i in range(streamline_len + 1):
                streamline_step_total_time = interval_start + i * streamline_step_time
                while step_index < len(trajectory) and trajectory[step_index].time_stamp < streamline_step_total_time:
                    step_index += 1
                    if step_index == len(trajectory):
                        break
                if step_index == len(trajectory):
                    self.append(None)
                else:
                    if step_index > 0:
                        prev_ratio, next_ratio = get_ratios(trajectory[step_index-1].time_stamp, trajectory[step_index].time_stamp, streamline_step_total_time)
                        next_streamline_step = trajectory[step_index-1].location * prev_ratio + trajectory[step_index].location * next_ratio
                    else:
                        next_streamline_step = trajectory[step_index].location
                    self.append(next_streamline_step)
                    self.closest_steps.append(step_index)

    def distance(self, streamline) -> float:
        if len(self) != len(streamline):
            raise RuntimeError("StreamLines must have the same length")
        f_total_distance = 0
        for i, s in enumerate(self):
            f_total_distance += streamline[i].dist(s)

        b_total_distance = 0
        for i, s in enumerate(self[::-1]):
            b_total_distance += streamline[i].dist(s)
            if b_total_distance > f_total_distance:
                return f_total_distance / len(self)
        return b_total_distance / len(self)


    @classmethod
    def combine(cls, streamlines):
        combined = StreamLine()
        for s in range(len(streamlines[0])):
            combined_step = Location()
            for sl in streamlines:
                combined_step += sl[s]
            combined_step.x /= len(streamlines)
            combined_step.y /= len(streamlines)
            combined.append(combined_step)
        return combined

    def clone(self):
        r = StreamLine()
        for s in self:
            r.append(Location(s.x, s.y))
        return r


class StreamLineCluster(JsonObject):

    def __iter__(self):
        return self.streamlines.__iter__()

    def __len__(self):
        return len(self.streamlines)

    def __init__(self, streamline: StreamLine = None):
        self.streamlines = JsonList(list_type=StreamLine)
        if streamline:
            self.streamlines.append(streamline)
            self.centroid = streamline
        else:
            self.centroid = StreamLine()
        JsonObject.__init__(self)

    def add_streamline(self, streamline: StreamLine, update_centroid: bool = True) -> None:
        if self.centroid and len(self.centroid) != len(streamline):
            raise RuntimeError("StreamLines must have the same length")
        if update_centroid:
            self.centroid = self.__get_new_centroid__(streamline)
        self.streamlines.append(streamline)

    def __get_new_centroid__(self, streamline: StreamLine) -> StreamLine:
        if not self.centroid:
            return streamline.clone()
        new_centroid = StreamLine()
        streamline_count = len(self.streamlines)
        for i, s in enumerate(self.centroid):
            combined_step = (streamline[i] + s * streamline_count) * (1 / (streamline_count + 1))
            new_centroid.append(combined_step)
        return new_centroid

    def distance(self, streamline: StreamLine, update_centroid=True) -> float:
        if update_centroid:
            new_centroid = self.__get_new_centroid__(streamline)
            return new_centroid.distance(streamline)
        else:
            return self.centroid.distance(streamline)

    def get_distances(self) -> JsonList:
        distances = JsonList(list_type=float)
        for sl in self.streamlines:
            distances.append(sl.distance(self.centroid))
        return distances


class StreamLineClusters(JsonObject):

    def __iter__(self):
        return self.clusters.__iter__()

    def __len__(self):
        return len(self.clusters)

    def __init__(self, min_clusters: int = 1, max_distance: float = .1, streamline_len: int = 100):
        self.min_clusters = min_clusters
        self.max_distance = max_distance
        self.streamline_len = streamline_len
        self.clusters = JsonList(list_type=StreamLineCluster)
        self.unclustered = JsonList(list_type=StreamLine)

    def evaluate_trajectory(self, trajectory: Trajectories) -> StreamLineCluster:
        streamline = StreamLine(trajectory=trajectory, streamline_len=self.streamline_len)
        return self.evaluate_streamline(streamline)

    def get_closest_cluster(self, streamline: StreamLine, update_centroid=True) ->tuple:
        if self.streamline_len + 1 != len(streamline):
            raise RuntimeError("StreamLines must have the same length")
        closest_cluster_distance = 0
        closest_cluster = None
        for c in self.clusters:
            distance = c.distance(streamline, update_centroid)
            if closest_cluster is None or distance < closest_cluster_distance:
                closest_cluster = c
                closest_cluster_distance = distance
        return closest_cluster, closest_cluster_distance

    def evaluate_streamline(self, streamline: StreamLine) -> StreamLineCluster:
        closest_cluster, closest_cluster_distance = self.get_closest_cluster(streamline, True)
        if closest_cluster_distance < self.max_distance:
            return closest_cluster
        else:
            return None

    def add_streamline(self, streamline: StreamLine) -> None:
        candidate_cluster = self.evaluate_streamline(streamline)
        if candidate_cluster is None:
            self.clusters.append(StreamLineCluster(streamline=streamline))
        else:
            candidate_cluster.add_streamline(streamline)

    def filter_clusters(self, threshold: int) -> None:
        self.unclustered = JsonList(list_type=StreamLine)
        while True:
            for i, c in enumerate(self.clusters):
                if len(c) < threshold:
                    break
            else:
                return
            self.unclustered += c
            self.clusters.remove(c)

    def streamline_count(self) -> int:
        counter = 0
        if self.unclustered:
            counter += len(self.unclustered)
        for c in self.clusters:
            counter += len(c.streamlines)
        return counter

    def add_trajectory(self, trajectory: Trajectories) -> None:
        streamline = StreamLine(trajectory=trajectory, streamline_len=self.streamline_len)
        self.add_streamline(streamline)

    def get_average_distance(self):
        distances = self.get_distances()
        if len(distances) == 0:
            return 0
        return sum(distances)/len(distances)

    def get_distances(self) -> JsonList:
        distances = self.get_intra_cluster_distances()
        for usl in self.unclustered:
            c, d = self.get_closest_cluster(usl, False)
            distances.append(d)
        return distances

    def get_intra_cluster_distances(self) -> JsonList:
        distances = JsonList(list_type=float)
        for c in self.clusters:
            distances += c.get_distances()
        return distances

    def get_average_intra_cluster_distance(self):
        distances = self.get_intra_cluster_distances()
        if len(distances) == 0:
            return 0
        return sum(distances)/len(distances)

    def get_cluster_population_standard_deviation(self):
        count = self.streamline_count()
        values = [len(c)/count for c in self.clusters]
        mean = sum(values)/len(values)
        dev = [abs(v-mean) ** 2 for v in values]
        std_dev = (sum(dev)/len(dev)) ** .5
        return std_dev

    def assign_unclustered(self):
        for u in self.unclustered:
            cc, d = self.get_closest_cluster(u)
            cc.add_streamline(u, update_centroid=False)
        self.unclustered.clear()