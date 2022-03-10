CREATE OR REPLACE FUNCTION opinr_add_m2m(table_name TEXT, first_column TEXT, second_column text, link_id int, ids int[]) RETURNS VOID AS
$$
DECLARE
    i integer;
BEGIN
    FOREACH i in array ids
    LOOP
        EXECUTE format('UPDATE %I SET %s = %s WHERE %s = %s and %s = %s;', table_name, first_column, link_id, first_column, link_id, second_column, i);
        IF found THEN
            CONTINUE;
        END IF;
        BEGIN
            EXECUTE format('INSERT INTO %I (%s, %s) VALUES (%s, %s);', table_name, first_column, second_column, link_id, i);
            CONTINUE;
        EXCEPTION WHEN unique_violation THEN
            CONTINUE;
        END;
    END LOOP;
    RETURN;
END;
$$
LANGUAGE plpgsql;

