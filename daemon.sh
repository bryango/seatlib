#!/bin/bash
# daemon that runs seatlib.py & notifies the user

# set -x  # for debug output

BROWSER=epiphany

if \
  data=$(poetry run ./seatlib.py)
  # data="文科图书馆 一层 C区	1/28	95"  # example debug input
then

  echo "match found:	$data"

  # make a sound
  paplay /usr/share/sounds/freedesktop/stereo/complete.oga &

  # make an array
  IFS=$'\t' read -r -a results <<< "$data"
  seatinfo="${results[0]}  [${results[1]}]"
  area_id=${results[2]}

  notify-send \
    "发现座位！ID: $area_id"\
    "$seatinfo" &
    # --hint=int:transient:1 &

  $BROWSER "https://seat.lib.tsinghua.edu.cn/cas/index.php?callback=https://seat.lib.tsinghua.edu.cn/home/web/f_second" &>/dev/null & disown
  sleep 0.5
  $BROWSER "https://seat.lib.tsinghua.edu.cn/web/seat3?area=$area_id" &>/dev/null & disown
fi
