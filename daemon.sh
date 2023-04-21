#!/bin/bash
# daemon that runs seatlib.py & notifies the user

BROWSER=epiphany

# set -x  # for debug output

cd "$(dirname "$(readlink -f "$0")")" || exit
$EDITOR ./prefs.yml

if \
  data=$(poetry run ./seatlib.py)
  # data="95	1/28	文科图书馆 一层 C区"  # example debug input
then

  echo "match found:	$data"

  # make a sound
  paplay /usr/share/sounds/freedesktop/stereo/complete.oga &

  # make an array
  IFS=$'\t' read -r -a results <<< "$data"
  area_id=${results[0]}
  seatinfo="${results[2]}  [${results[1]}]"

  notify-send \
    "发现座位！ID: $area_id"\
    "$seatinfo" &
    # --hint=int:transient:1 &

  $BROWSER "https://seat.lib.tsinghua.edu.cn/cas/index.php?callback=https://seat.lib.tsinghua.edu.cn/home/web/f_second" &>/dev/null & disown
  sleep 0.5
  $BROWSER "https://seat.lib.tsinghua.edu.cn/web/seat3?area=$area_id" &>/dev/null & disown
fi
