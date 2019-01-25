
建用户表
create table user_t(
    id int NOT NULL AUTO_INCREMENT,
    userName varchar(20) NOT NULL unique,
    realName varchar(20),
    createTime datetime,
    PRIMARY KEY (id)
);

建签到表
create table check_t(
    id int NOT NULL AUTO_INCREMENT,
    userName varchar(20) NOT NULL,
    checkInDate date,
    checkInTime datetime,
    cameraNumber smallint NOT NULL DEFAULT 0,
    PRIMARY KEY (id)
);

每日统计表
create table sum_t(
    id int NOT NULL AUTO_INCREMENT,
    userName varchar(20) NOT NULL,
    checkInDate date,
    totalTime float,
    PRIMARY KEY (id)
);