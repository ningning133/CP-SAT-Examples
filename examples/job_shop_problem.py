"""Minimal jobshop example (refactored with logging and separated solve/output)."""
import collections
from utils.logger_config import setup_logger
from ortools.sat.python import cp_model

# ===========================
# Logging Configuration
# ===========================
logger = setup_logger(logger_name="jsp")

# Data Class
class Data:
    def __init__(self, _jobs_data):
        self.jobs_data = jobs_data
        self.machines_count = 1 + max(task[0] for job in _jobs_data for task in job)
        self.all_machines = range(self.machines_count)
        self.horizon = sum(task[1] for job in _jobs_data for task in job)


# Model Class
class JSPModel:
    def __init__(self, data: Data):
        self.data = data
        self.model = cp_model.CpModel()
        self.solver = None
        self.status = None

    # -----------------------
    # Variables
    def createVars(self):
        # Tips：namedtuple 是 Python 标准库 collections 提供的一种轻量级数据结构。
        # 它的作用是：创建一个“像 tuple 一样轻量，但像对象一样可读”的结构。
        task_type = collections.namedtuple("task_type", "start end interval")

        self.all_tasks = {}
        self.machine_to_intervals = collections.defaultdict(list)

        for job_id, job in enumerate(self.data.jobs_data):
            for task_id, task in enumerate(job):
                machine, duration = task
                suffix = f"_{job_id}_{task_id}"

                start_var = self.model.new_int_var(
                    0, self.data.horizon, "start" + suffix
                )
                end_var = self.model.new_int_var(
                    0, self.data.horizon, "end" + suffix
                )
                interval_var = self.model.new_interval_var(
                    start_var, duration, end_var, "interval" + suffix
                )

                self.all_tasks[job_id, task_id] = task_type(
                    start=start_var, end=end_var, interval=interval_var
                )
                self.machine_to_intervals[machine].append(interval_var)

    # -----------------------
    # Constraints
    def createConstrs(self):
        # Machine no-overlap
        for machine in self.data.all_machines:
            self.model.add_no_overlap(self.machine_to_intervals[machine])

        # Precedence
        for job_id, job in enumerate(self.data.jobs_data):
            for task_id in range(len(job) - 1):
                self.model.add(
                    self.all_tasks[job_id, task_id + 1].start
                    >= self.all_tasks[job_id, task_id].end
                )

    # -----------------------
    # Objective
    def createObj(self):
        obj_var = self.model.new_int_var(0, self.data.horizon, "makespan")

        self.model.add_max_equality(
            obj_var,
            [
                self.all_tasks[job_id, len(job) - 1].end
                for job_id, job in enumerate(self.data.jobs_data)
            ],
        )

        self.model.minimize(obj_var)
        self.obj_var = obj_var

    # -----------------------
    # Solve
    def solve(self):
        logger.info("Start solving model...")
        self.solver = cp_model.CpSolver()
        self.status = self.solver.solve(self.model)

        if self.status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logger.info("Solve finished successfully.")
        else:
            logger.warning("No solution found.")

        return self.status

    # -----------------------
    # Extract Solution
    def extract_solution(self):
        if self.status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None

        assigned_task_type = collections.namedtuple(
            "assigned_task_type", "start job index duration"
        )

        assigned_jobs = collections.defaultdict(list)

        for job_id, job in enumerate(self.data.jobs_data):
            for task_id, task in enumerate(job):
                machine = task[0]
                assigned_jobs[machine].append(
                    assigned_task_type(
                        start=self.solver.value(
                            self.all_tasks[job_id, task_id].start
                        ),
                        job=job_id,
                        index=task_id,
                        duration=task[1],
                    )
                )

        return assigned_jobs

    # -----------------------
    # Format Solution
    def format_solution(self, assigned_jobs):
        output = ""
        for machine in self.data.all_machines:
            assigned_jobs[machine].sort()
            sol_line_tasks = f"Machine {machine}: "
            sol_line = " " * 11

            for assigned_task in assigned_jobs[machine]:
                name = f"job_{assigned_task.job}_task_{assigned_task.index}"
                sol_line_tasks += f"{name:15}"

                start = assigned_task.start
                duration = assigned_task.duration
                sol_tmp = f"[{start},{start + duration}]"
                sol_line += f"{sol_tmp:15}"

            sol_line += "\n"
            sol_line_tasks += "\n"
            output += sol_line_tasks + sol_line

        return output

    # -----------------------
    # Log Solution
    def log_solution(self):
        if self.status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logger.warning("No feasible solution to log.")
            return

        assigned_jobs = self.extract_solution()
        formatted_output = self.format_solution(assigned_jobs)

        logger.info(f"Optimal Schedule Length: {self.solver.objective_value}")
        logger.info("\n" + formatted_output)

    # -----------------------
    # Run
    # -----------------------
    def run_model(self):
        self.createVars()
        self.createConstrs()
        self.createObj()
        self.solve()
        self.log_solution()


# ===========================
# Main
if __name__ == "__main__":
    jobs_data = [
        [(0, 3), (1, 2), (2, 2)],
        [(0, 2), (2, 1), (1, 4)],
        [(1, 4), (2, 3)],
    ]

    data = Data(_jobs_data=jobs_data)
    model = JSPModel(data=data)
    model.run_model()