from datetime import datetime, timezone
from typing import Optional
from tzlocal import get_localzone
import time
import calendar
from pydantic import BaseModel, Field

class Timestamp(BaseModel):
    unix_timestamp_utc: float = Field(...,
                                      description="The date and time in Coordinated Universal Time (UTC), presented as the number of seconds since January 1, 1970")
    unix_timestamp_local: float = Field(...,
                                        description="The date and time in the local timezone, presented as the number of seconds since January 1, 1970")
    unix_timestamp_utc_isoformat: str = Field(...,
                                              description="The date and time in Coordinated Universal Time (UTC - a time standard used across the world), formatted according to the international standard ISO 8601")
    unix_timestamp_local_isoformat: str = Field(...,
                                                description="The date and time in the local timezone, formatted according to the international standard ISO 8601")
    perf_counter_ns: Optional[int] = Field(None,
                                           description="The time elapsed since an arbitrary point (such as the start of the program or when the `time` module was loaded), measured in nanoseconds to avoid floating-point error. This provides a high-precision time useful for timing or profiling code execution.")
    local_time_zone: str = Field(..., description="The key or name representing the local timezone")
    human_readable_utc: str = Field(..., description="The date and time in Coordinated Universal Time (UTC), presented in a more human-readable format, e.g., 'YYYY-MM-DD HH:MM:SS.ssssss'")
    human_readable_local: str = Field(..., description="The date and time in the local timezone, presented in a more human-readable format, e.g., 'YYYY-MM-DD HH:MM:SS.ssssss'")
    day_of_week: str = Field(..., description="The day of the week, e.g., 'Monday'")
    calendar_week: int = Field(..., description="The calendar week of the year")
    day_of_year: int = Field(..., description="The day number of the year")
    is_leap_year: bool = Field(..., description="Indicates whether the year is a leap year or not")

    def __init__(self, date_time: Optional[datetime] = None, perf_counter_ns: Optional[int] = None):
        """
        Initialize the Timestamp object.

        Args:
            date_time (datetime, optional): Input datetime object. Defaults to current datetime if not provided.
            perf_counter_ns (int, optional): Performance counter value in nanoseconds. If not provided and datetime is
            not provided, defaults to the time taken for object initialization.
        """
        if date_time is None:
            date_time_utc = datetime.utcnow()
            date_time_local = datetime.now()
            perf_counter_ns = time.perf_counter_ns() if perf_counter_ns is None else perf_counter_ns
        else:
            date_time_utc = date_time.astimezone(timezone.utc)
            date_time_local = date_time.astimezone(get_localzone())

        unix_timestamp_utc = date_time_utc.timestamp()
        unix_timestamp_local = date_time_local.timestamp()
        unix_timestamp_utc_isoformat = date_time_utc.isoformat()
        unix_timestamp_local_isoformat = date_time_local.isoformat()
        local_time_zone = str(get_localzone())
        human_readable_utc = date_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
        human_readable_local = date_time_local.strftime('%Y-%m-%d %H:%M:%S.%f')
        day_of_week = calendar.day_name[date_time_local.weekday()]
        calendar_week = date_time_local.isocalendar()[1]
        day_of_year = date_time_local.timetuple().tm_yday
        is_leap_year = calendar.isleap(date_time_local.year)

        super().__init__(unix_timestamp_utc=unix_timestamp_utc,
                         unix_timestamp_local=unix_timestamp_local,
                         unix_timestamp_utc_isoformat=unix_timestamp_utc_isoformat,
                         unix_timestamp_local_isoformat=unix_timestamp_local_isoformat,
                         perf_counter_ns=perf_counter_ns,
                         local_time_zone=local_time_zone,
                         human_readable_utc=human_readable_utc,
                         human_readable_local=human_readable_local,
                         day_of_week=day_of_week,
                         calendar_week=calendar_week,
                         day_of_year=day_of_year,
                         is_leap_year=is_leap_year)


if __name__ == "__main__":
    from pprint import pprint as print
    print("Printing `Timestamp()` object:")
    print(Timestamp())
    print("\nPrinting `Timestamp(timezone.now())`:")
    print(Timestamp(datetime.now()))




