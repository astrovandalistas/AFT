# run AFT stuff
export DISPLAY=':0.0'
amiterminal=`who am i | grep tty | wc -l`
if [ $amiterminal -gt 0 ]
then
    startx &
fi

isrun=`ps -u tgh | grep python | wc -l`
if [ $isrun -lt 1 ]
then
    cd /home/pi/Dev/AFT
    ##python AFT.py
while [ 1 -le 20 ]
do
    python AFT.py
    killpid=$!
    sleep 666
    kill -9 $killpid
done
