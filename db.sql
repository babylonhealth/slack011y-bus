CREATE TABLE requests (
    id int AUTO_INCREMENT PRIMARY KEY,
    slack_channel_name varchar(80) NOT NULL,
    slack_channel_id varchar(64) NOT NULL,
    title varchar(4000),
    request_status varchar(64) NOT NULL,
    requestor_id varchar(64) NOT NULL,
    requestor_email varchar(64) NOT NULL,
    requestor_team_id varchar(64),
    event_ts DECIMAL(16, 6) NOT NULL,
    start_datetime_utc datetime,
    start_work_datatime_utc datetime,
    completion_datetime_utc datetime,
    request_type_list varchar(1000),
    request_link varchar(255),
    labels varchar(1000),
    completion_reactions JSON,
    form_answers JSON,
    request_types JSON,
    autoclose_status varchar(64),
    blocks_id INT
);

CREATE TABLE thread_messages (
    id int AUTO_INCREMENT PRIMARY KEY,
    author_id varchar(64) NOT NULL,
    thread_ts DECIMAL(16, 6) NULL,
    event_ts DECIMAL(16, 6) NOT NULL,
    event_datetime_utc datetime,
    request_table_id int not null,
    blocks_id INT,
    foreign key (request_table_id) references requests(id)
);

CREATE TABLE control_panels (
    id int AUTO_INCREMENT PRIMARY KEY,
    slack_channel_name varchar(80) NOT NULL,
    slack_channel_id varchar(64) NOT NULL,
    creation_ts DECIMAL(16, 6) NOT NULL,
    deactivation_ts DECIMAL(16, 6),
    label_questions varchar(1000),
    form_questions JSON,
    channel_properties JSON
);

CREATE TABLE distributed_lock(
  id int PRIMARY KEY AUTO_INCREMENT,
  lock_type varchar(255) NOT NULL UNIQUE,
  bot_instance varchar(255) NOT NULL,
  last_heartbeat_utc datetime NOT NULL
);

CREATE TABLE blocks (id int primary key auto_increment, blocks json not null);

CREATE INDEX ind_blocks_id on requests(blocks_id);
CREATE INDEX ind_blocks_id on thread_messages(blocks_id);


DELIMITER //
CREATE FUNCTION channel_time_to_complete_percentile(
    event_ts_from decimal(16,6),
    event_ts_to decimal(16,6),
    tool_type varchar(100),
    percentile int)
RETURNS decimal(16,6)
NOT DETERMINISTIC
READS SQL DATA
SQL SECURITY INVOKER
BEGIN
DECLARE result DECIMAL(16,6);
SELECT time_to_complete / 60 as time_to_complete_hours FROM
    (SELECT t.*,
        timestampdiff(minute, start_datetime_utc, completion_datetime_utc) as time_to_complete,
        @row_num :=@row_num + 1 AS row_num
        FROM requests t, (SELECT @row_num:=0) counter
    where t.event_ts between event_ts_from AND event_ts_to
        AND request_status = "COMPLETED"
        AND IF ( tool_type = "all", 1=1, JSON_CONTAINS(request_type_list, tool_type, '$.message'))
    ORDER BY time_to_complete)
temp WHERE temp.row_num = ROUND ((percentile / 100) * @row_num) into result;
RETURN result;
END //
DELIMITER ;

--13.09.2022
DELIMITER //
CREATE FUNCTION JSON_UNIQ(arr JSON) RETURNS json
DETERMINISTIC
NO SQL
SQL SECURITY INVOKER
BEGIN

  SET @arr = arr;
  SET @a_length = JSON_LENGTH(@arr);
  SET @loop_index = @a_length;
    
    WHILE @loop_index >= 0 DO

      SET @item = JSON_UNQUOTE(JSON_EXTRACT(@arr, concat('$[',@loop_index,']')));
      SET @itemcount = coalesce(JSON_LENGTH(JSON_SEARCH(@arr, 'all', @item)), 0);

      IF @itemcount > 1 THEN
        SET @arr = JSON_REMOVE(@arr, CONCAT('$[',@loop_index,']'));
        SET @loop_index = @loop_index - 1;
      END IF;

      SET @loop_index = @loop_index - 1;

    End WHILE;

    RETURN CAST(@arr AS JSON);

END //
DELIMITER ;
