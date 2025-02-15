import duckdb

import equalexperts_dataeng_exercise.config as cfg

DB_FULL_NAME = cfg.DB_FULL_NAME
VIEW_NAME = cfg.VIEW_NAME
FULL_VIEW_NAME = cfg.FULL_VIEW_NAME
DB_TABLE_FULL_NAME = cfg.DB_TABLE_FULL_NAME

sql_outlier_query = f"""DROP VIEW IF EXISTS {FULL_VIEW_NAME};
    CREATE VIEW {FULL_VIEW_NAME} AS
    WITH yearly_vote_count AS (
    SELECT
        EXTRACT(YEAR FROM CreationDate) AS year,
        COUNT(DISTINCT EXTRACT(WEEK FROM CreationDate)) AS total_weeks,
        COUNT(Id) AS total_vote_count,
    FROM {DB_TABLE_FULL_NAME}
        GROUP BY year
        ),
    weekly_vote_count AS (
        SELECT
            EXTRACT(YEAR FROM CreationDate) AS year,
            CASE
                WHEN MONTH(CreationDate) = 1 and Day(CreationDate) < 10 and WEEK(CreationDate) > 45 Then 0
                WHEN MONTH(CreationDate) = 12 and Day(CreationDate) > 20 and WEEK(CreationDate) < 10 Then WEEK(CreationDate - INTERVAL 4 DAY) + 1
                ELSE EXTRACT(WEEK FROM CreationDate)
            END AS week_number,
            COUNT(*) AS weekly_vote_count
        FROM {DB_TABLE_FULL_NAME}
        GROUP BY year, week_number
    ),
    outlier_cal AS (
    select w.year, w.week_number, w.weekly_vote_count,
        ABS(1 - (w.weekly_vote_count / (y.total_vote_count / y.total_weeks))) AS weekly_vote_ratio,
        CASE
            WHEN weekly_vote_ratio > 0.2 then TRUE
            ELSE FALSE
        END as filter_param
            from weekly_vote_count w join yearly_vote_count y on w.year = y.year )
    SELECT Year as Year, week_number as WeekNumber, weekly_vote_count as VoteCount  FROM outlier_cal
    WHERE filter_param = TRUE
    ORDER BY year ASC, week_number ASC
    """


def get_outlier_week():
    """ Connect to the database and get the outlier weeks """
    try:
        conn = duckdb.connect(DB_FULL_NAME)
        conn.execute(sql_outlier_query).fetchall()
        view_query = f"SELECT * from {FULL_VIEW_NAME}"
        outlier_table = conn.execute(view_query).fetchall()
        column_names = [desc[0] for desc in conn.description]
        print(f"Summary, Number of rows :{len(outlier_table)}")
        print(column_names)

        for r in outlier_table:
            print(r)
    except Exception as ex:
        print(f"Error : {ex}")
        raise
    finally:
        conn.close()


def run_main_outlier():
    get_outlier_week()


if __name__ == "__main__":
    print("Start main outlier")
    run_main_outlier()
    print("End main outlier")
