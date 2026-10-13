class ConsoleNotificationProvider:
    async def send(self, subject: str, body: str):
        print("=" * 60)
        print("CCTV NOTIFICATION")
        print(subject)
        print(body)
        print("=" * 60)


async def notify_alarm(alarm, event):
    provider = ConsoleNotificationProvider()
    await provider.send(
        subject=f"CCTV Alarm: {event.event_type}",
        body=(
            f"Camera: {event.camera_id}\n"
            f"Severity: {alarm.severity}\n"
            f"Snapshot: {event.snapshot_url or 'none'}"
        ),
    )
