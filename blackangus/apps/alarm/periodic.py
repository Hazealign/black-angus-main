import logging

import pendulum
from discord import Client, Embed

from blackangus.apps.base import BasePeriodicApp
from blackangus.config import Config
from blackangus.models.alarm import AlarmModel
from blackangus.utils.crontab import get_next_crontab_time


# 매 분마다 도는 멍청한 짓을 하지만,
# 우선은 하나하나 일정하게 crontab을 등록할 수 없으니 이렇게 구현한다.
class AlarmPeriodicApp(BasePeriodicApp):
    period = '* * * * *'
    disabled = False

    def __init__(self, config: Config, client: Client):
        self.config = config
        self.client = client

    async def action(self):
        # 기준 시간과 알람 목록을 가져오고
        current_time = pendulum.now(tz='Asia/Seoul')
        alarms = await AlarmModel.find(
            {
                'enabled': True,
            }
        ).to_list()

        logging.info(f'총 알람 {len(alarms)}개 체크')

        # 울려야할 알람 목록을 가져온 뒤,
        targets = []
        for alarm in alarms:
            alarm_time = pendulum.instance(alarm.time, tz='Asia/Seoul')
            if alarm_time.timestamp() <= current_time.timestamp():
                targets.append(alarm)

        logging.info(f'알람 실행 {len(targets)}개')

        # 하나씩 알람을 실행한다.
        for alarm in targets:
            logging.info(f'{alarm.created_by}의 {alarm.name} 알람 실행 중...')
            if not alarm.is_repeat:
                # 반복되지 않는 알람은 꺼버리고
                alarm.enabled = False
                alarm.last_activated_at = current_time
                await alarm.replace()
            else:
                # 반복하는 알람은 울려야할 다음 시간으로 변경한다.
                alarm.time = get_next_crontab_time(current_time, alarm.crontab)
                alarm.last_activated_at = current_time
                await alarm.replace()

            # 어느쪽이든 메세지를 보내줘야한다.
            await self.client.get_channel(alarm.channel_id).send(
                content=f'<@{alarm.created_by}>',
                embed=Embed(
                    title=alarm.name,
                    description=alarm.content,
                ).set_footer(text='흑우에 등록한 알람이 작동하였습니다.'),
            )

        logging.info('알람 실행 완료!')
