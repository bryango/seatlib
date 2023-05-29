#!/bin/bash
# daemon that runs seatlib.py & notifies the user

## this script is designed to run seatlib.py directly
## ... without installation

BROWSER=epiphany

# set -x  # for debug output

cd "$(dirname "$(readlink -f "$0")")" || exit

while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--no-prefs)
      NO_PREFS=YES
      shift
      ;;
    *)
      shift
      ;;
  esac
done

if [[ -z $NO_PREFS ]]; then
  $EDITOR ./config/prefs.yml
fi

( nohup $BROWSER &>/dev/null & disown ) &>/dev/null & disown

if \
  data=$(poetry run ./seatlib.py)
  # data="15:00:16	95	1/28	文科图书馆 一层 C区	area=95&segment=1593416&day=2023-5-8&startTime=10:24&endTime=22:00"  # example debug input
then

  echo "$data"

  # make a sound
  paplay /usr/share/sounds/freedesktop/stereo/complete.oga &

  # make an array
  IFS=$'\t' read -r -a results <<< "$data"
  area_id=${results[1]}
  seatinfo="${results[3]}  [${results[2]}]"
  datetime_string=${results[4]}
  target_url="https://seat.lib.tsinghua.edu.cn/web/seat3?area=$area_id&$datetime_string"

  notify-send \
    "发现座位！$seatinfo"\
    "$target_url" &
    # --hint=int:transient:1 &

  $BROWSER "https://seat.lib.tsinghua.edu.cn/cas/index.php?callback=https://seat.lib.tsinghua.edu.cn/home/web/f_second" &>/dev/null & disown
  sleep 0.5
  $BROWSER "$target_url" &>/dev/null & disown
fi
