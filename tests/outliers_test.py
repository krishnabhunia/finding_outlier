import subprocess
import pytest
import os
import duckdb
import tests.config_test as cfg
import equalexperts_dataeng_exercise.outliers as ol
import logging

logger = logging.getLogger()

VIEW_NAME = cfg.VIEW_NAME
FULL_VIEW_NAME = cfg.FULL_VIEW_NAME
DB_SCHEMA_NAME = cfg.DB_SCHEMA_NAME
DB_NAME = cfg.DB_NAME
DB_FULL_NAME = cfg.DB_FULL_NAME
FILE_NAME = cfg.FILE_NAME


def run_outliers_calculation():
    result = subprocess.run(
        args=["python", "-m", "equalexperts_dataeng_exercise.outliers"],
        capture_output=True,
    )
    result.check_returncode()


def run_ingestion():
    result = subprocess.run(
        args=[
            "python",
            "-m",
            "equalexperts_dataeng_exercise.ingest",
            f"{FILE_NAME}",
        ],
        capture_output=True,
    )
    result.check_returncode()


def test_check_view_exists():
    sql = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_type='VIEW' AND table_name='{VIEW_NAME}' AND table_schema='{DB_SCHEMA_NAME}' AND table_catalog='{DB_NAME}';
    """
    try:
        run_ingestion()
        run_outliers_calculation()
        con = duckdb.connect(DB_FULL_NAME, read_only=True)
        result = con.execute(sql).fetchall()
        assert len(result) == 1, "Expected view 'outlier_weeks' to exist"
    except Exception as ex:
        print(f"Error : {ex}")
        assert False
    finally:
        con.close()


def test_check_view_has_data():
    try:
        sql = f"SELECT COUNT(*) FROM {FULL_VIEW_NAME}"
        run_ingestion()
        run_outliers_calculation()
        con = duckdb.connect(DB_FULL_NAME, read_only=True)
        result = con.execute(sql).fetchall()
        assert len(result) > 0, "Expected view 'outlier_weeks' to have data"
    finally:
        con.close()


def test_check_view_data_rows_check():
    sql = f"SELECT * FROM {FULL_VIEW_NAME}"
    try:
        run_ingestion()
        run_outliers_calculation()
        con = duckdb.connect(DB_FULL_NAME, read_only=True)
        result = con.execute(sql).fetchall()
        if FILE_NAME == "tests/test-resources/samples-votes.jsonl":
            assert len(result) == 6, "Expected view 'outlier_weeks' to have specific number of rows data"
        elif FILE_NAME == "tests/test-resources/votes.jsonl":
            assert len(result) == 144, "Expected view 'outlier_weeks' to have specific number of rows data"

        # Check if the year is in ascending order
        first_year = result[0][0]
        last_year = result[-1][0]
        assert first_year <= last_year, "Expected view 'outlier_weeks' to have data in ascending order"

        # Check if the week is in ascending order
        if len(result) >= 2:
            prev = result[0]
            for next in result[1:]:
                if prev[0] == next[0]:
                    assert prev[1] <= next[1], "Expected view 'outlier_weeks' to have weekly number in ascending order"
                else:
                    assert prev[0] <= next[0], "Expected view 'outlier_weeks' to have year in ascending order"
                prev = next

    except Exception as ex:
        print(f"Error : {ex}")
        assert False
    finally:
        con.close()


def test_check_exception():
    if os.path.exists(DB_FULL_NAME):
        os.remove(DB_FULL_NAME)
    with pytest.raises(Exception) as ex:
        ol.get_outlier_week()
    assert ex.typename == 'CatalogException', "Expecting a CatalogException: Schema with name blog_analysis does not exist!'"
