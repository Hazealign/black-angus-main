from datetime import datetime

import pendulum
from croniter import croniter


def get_next_crontab_time(
    base_time: pendulum.DateTime,
    crontab: str,
) -> pendulum.DateTime:
    """
    주어진 crontab string으로 다음 알람 시간을 구합니다.

    :param base_time: 기준 시간
    :param crontab: 크론탭 문자열
    :return: 다음 알람 시간
    """
    return pendulum.instance(
        croniter(crontab, base_time).get_next(datetime), tz='Asia/Seoul'
    )
