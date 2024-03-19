DROP TABLE IF EXISTS rtk_one_min;
CREATE TABLE rtk_one_min ( 
    time TIMESTAMP(6) WITHOUT TIME ZONE NOT NULL, 
    base  CHARACTER VARYING(4) NOT NULL, 
    rover CHARACTER VARYING(4) NOT NULL, 
    n     REAL, 
    e     REAL, 
    u     REAL, 
    q     SMALLINT, 
    sdn   REAL, 
    sde   REAL, 
    sdu   REAL, 
    sden  REAL, 
    sdnu  REAL, 
    sdue  REAL, 
    PRIMARY KEY (base, rover, time) 
);

SELECT create_hypertable("rtk_one_min", "time");

COMMENT ON TABLE rtk_one_min IS 'One minute resamples of RTK(Real-time kinematic positioning) baselines.';
COMMENT ON COLUMN rtk_one_min.time IS 'Time of observation';
COMMENT ON COLUMN rtk_one_min.base IS 'The base station';
COMMENT ON COLUMN rtk_one_min.rover IS 'The station that is moving relative to the base station';
COMMENT ON COLUMN rtk_one_min.n IS 'The north component of the motion';
COMMENT ON COLUMN rtk_one_min.e IS 'The east component of the motion';
COMMENT ON COLUMN rtk_one_min.u IS 'The up component of the motion';
COMMENT ON COLUMN rtk_one_min.q IS 'Integer indicating the quality of the observation. 1: fixed, 2: float, 3:sbas, 4:dgps, 5:single, 6: ppp';
COMMENT ON COLUMN rtk_one_min.sdn IS 'Variance of the north component';
COMMENT ON COLUMN rtk_one_min.sde IS 'Variance of the east component';
COMMENT ON COLUMN rtk_one_min.sdu IS 'Variance of the up component';
COMMENT ON COLUMN rtk_one_min.sden IS 'Covariance of the east and north components';
COMMENT ON COLUMN rtk_one_min.sdnu IS 'Covariance of the north and up components';
COMMENT ON COLUMN rtk_one_min.sdue IS 'Covariance of the up and east components';
