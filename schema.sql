CREATE RETENTION POLICY "1_week" ON "kcam"  DURATION 1w  REPLICATION 1 DEFAULT
CREATE RETENTION POLICY "1_year" ON "kcam"  DURATION 52w REPLICATION 1
CREATE RETENTION POLICY "forever" ON "kcam" DURATION inf REPLICATION 1

CREATE CONTINUOUS QUERY "temp_15" on "kcam" BEGIN SELECT mean("temperature") AS "temperature", mean("humidity") AS "humidity" INTO "1_year"."temperature" FROM "temperature" GROUP BY time(15m) END
CREATE CONTINUOUS QUERY "temp_60" on "kcam" BEGIN SELECT mean("temperature") AS "temperature", mean("humidity") AS "humidity" INTO "forever"."temperature" FROM "temperature" GROUP BY time(30m) END

CREATE CONTINUOUS QUERY "mot_15" on "kcam" BEGIN SELECT count("value") AS "value" INTO "1_year"."motion" FROM "motion" GROUP BY time(15m) END

