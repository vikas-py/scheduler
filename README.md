It's an excellent idea to create a comprehensive design document to formalize our plans. Since you mentioned Google Docs, I'll provide a full, in-depth design specification that you can copy and paste directly into a document to begin the project.

-----

### **Design Specification: Filling Line Scheduling Tool**

#### 1\. Introduction

This document serves as the design specification for a Python-based tool aimed at optimizing the scheduling of a product filling line. The core objective is to minimize total production time by intelligently reordering batches based on a set of constraints and changeover penalties. This specification outlines the project's architecture, data models, and algorithms, providing a comprehensive blueprint for development.

#### 2\. Problem Statement

The tool must generate a filling schedule that completes all batches in the shortest time, adhering to the following rules:

  * **Filling Rate:** Constant at **332 vials per minute**.
  * **Changeovers:** **4 hours** for same-type batches and **8 hours** for different-type batches.
  * **Reclean Cycle:** A mandatory **24-hour** line clean is required at the start and after every **120 hours** of continuous use.
  * **Batch Integrity:** Batches must be filled consecutively and cannot be split.

The final output should be an actionable schedule for a manufacturing team and a report detailing the performance of the generated schedule.

\<br\>
\<br\>

-----

#### 3\. Architecture and Design

The solution is built on a modular architecture, separating concerns into dedicated files and directories.

```
/filling_schedule_optimizer/
├── __init__.py
├── config.py
├── main.py
├── models.py
├── output.py
├── validation.py
├── reports/
│   └── schedule_report.html
├── data/
│   └── example_lots.csv
└── strategies/
    ├── __init__.py
    ├── fifo.py
    ├── hybrid_heuristic.py
    └── spt_only.py
```

  * **`main.py`**: The **command-line workflow engine**. It orchestrates the entire process: loading configuration, ingesting and validating data, generating the schedule with a chosen strategy, and producing the final report. It provides clear, step-by-step progress updates to the user.
  * **`config.py`**: A centralized **configuration file** that stores all modifiable parameters, constraints, and file paths. This eliminates hard-coding and makes the tool highly adaptable.
  * **`models.py`**: Defines the **data structures**. The `Lot` class represents a single batch, and the `ScheduleEntry` class represents a single event in the schedule (e.g., filling a lot, a changeover).
  * **`validation.py`**: A module dedicated to **data validation**. Its `validate_lots()` function checks for missing fields, invalid data types, non-positive values, and duplicate IDs, ensuring data integrity before processing.
  * **`strategies/`**: A package that contains all **scheduling heuristic implementations**. Each strategy is in its own file, allowing for easy expansion and comparison.

\<br\>
\<br\>

-----

#### 4\. Scheduling Strategies

The tool will feature three distinct scheduling algorithms, which can be selected via configuration.

##### 4.1. Hybrid Heuristic (`strategies/hybrid_heuristic.py`)

This is the core, optimized solution. It combines three key principles:

1.  **Grouping:** Batches are first grouped by `type` to minimize costly 8-hour changeovers.
2.  **Shortest Processing Time (SPT):** Within each group, lots are sorted by filling time (vials / filling rate) from shortest to longest.
3.  **Greedy Logic:** The algorithm determines which group to run first by a greedy rule (e.g., the group with the largest total run time), ensuring maximum efficiency. The schedule is built by sequentially adding lots, inserting 4-hour changeovers between same-type lots and a single 8-hour changeover when transitioning between groups. Recleans are inserted whenever the cumulative line usage exceeds the 120-hour limit.

##### 4.2. SPT Only (`strategies/spt_only.py`)

This serves as a benchmark. It sorts all lots by filling time, disregarding their type, and then schedules them. This strategy will highlight the value of type-based grouping.

##### 4.3. FIFO (`strategies/fifo.py`)

This is the simplest, non-optimized strategy. It processes lots in the exact order they appear in the input data, serving as a baseline to demonstrate the performance improvements of the other heuristics.

\<br\>
\<br\>

-----

#### 5\. Reporting

Reporting is handled by the `output.py` module and a dedicated `reports/` directory.

##### 5.1. HTML Report Generation

  * The `output.py` module will contain a `generate_html_report()` function.
  * This function will dynamically build a single HTML string using Python's f-strings, without external libraries like Jinja2.
  * The report will include a summary table of key metrics (**Total Time**, **Total Changeover Time**, **Total Reclean Time**) and a detailed, step-by-step schedule table.
  * The final HTML file will be saved in the `reports/` directory.

\<br\>
\<br\>

-----

#### 6\. Implementation and Execution Flow

1.  **Main Function Execution:** `main.py` is executed from the command line.
2.  **Configuration and Data Loading:** The program reads parameters from `config.py` and loads data from `data/example_lots.csv`.
3.  **Validation:** The `validation.py` module checks the data's integrity.
4.  **Strategy Execution:** Based on the configuration, `main.py` calls the appropriate function from the `strategies/` directory to generate the schedule.
5.  **Report Generation:** The resulting schedule is passed to `output.py` to produce the HTML report.
6.  **Termination:** The program provides a final confirmation message and gracefully exits.
