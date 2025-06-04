CREATE TABLE IF NOT EXISTS circuits (
    circuit_id VARCHAR(255) PRIMARY KEY,
    circuit_name TEXT,
    locality VARCHAR(255),
    country VARCHAR(255)
);
COMMENT ON TABLE circuits IS 'Table containing circuits information.';

CREATE TABLE IF NOT EXISTS races (
    race_id VARCHAR(255) PRIMARY KEY,
    year INTEGER NOT NULL,
    round INTEGER NOT NULL,
    race_name TEXT,
    circuit_id VARCHAR(255) REFERENCES circuits(circuit_id),
    date DATE,
    time TIME,
    circuit_name_denorm TEXT,
    circuit_locality_denorm VARCHAR(255),
    circuit_country_denorm VARCHAR(255),
    CONSTRAINT unique_race_in_season UNIQUE (year, round)
);
COMMENT ON TABLE races IS 'Information on each race in a season.';

CREATE TABLE IF NOT EXISTS drivers (
    driver_id VARCHAR(255) PRIMARY KEY,
    permanent_number INTEGER,
    code VARCHAR(10) UNIQUE,
    given_name TEXT NOT NULL,
    family_name TEXT NOT NULL,
    date_of_birth DATE,
    nationality VARCHAR(255)
);
COMMENT ON TABLE drivers IS 'F1 drivers information.';

CREATE TABLE IF NOT EXISTS constructors (
    constructor_id VARCHAR(255) PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    nationality VARCHAR(255)
);
COMMENT ON TABLE constructors IS 'F1 constructors information.';

CREATE TABLE IF NOT EXISTS results (
    result_id SERIAL PRIMARY KEY,
    race_id VARCHAR(255) NOT NULL REFERENCES races(race_id),
    driver_id VARCHAR(255) NOT NULL REFERENCES drivers(driver_id),
    constructor_id VARCHAR(255) NOT NULL REFERENCES constructors(constructor_id),
    car_number INTEGER,
    grid_position INTEGER,
    final_position INTEGER,
    position_text VARCHAR(10),
    points FLOAT,
    laps_completed INTEGER,
    status VARCHAR(255),
    time_millis VARCHAR(255),
    time_text VARCHAR(255),
    CONSTRAINT unique_result_per_driver_per_race UNIQUE (race_id, driver_id)
);
COMMENT ON TABLE results IS 'Detailed results for each pilot of each race.';