while :
do
  stillRunning=$(ps -ef |grep "python -u camera_handler.py" |grep -v "grep")
  if [ "$stillRunning" ] ; then
    echo "TWS service was already started by another way" 
    #kill -9 $pidof /usr/src/face_check/camera_handler.py
  else
    echo "TWS service was not started" 
    echo "Starting service ..." 
	sudo nohup python -u camera_handler.py > face.log 2>&1 &    
    echo "TWS service was exited!" 
  fi
  sleep 30
done

