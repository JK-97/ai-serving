from multiprocessing import Queue, Value

input_queue   = Queue(maxsize=25)
predp_queue   = Queue(maxsize=25)
predict_queue = Queue(maxsize=25)
output_queue  = Queue(maxsize=25)

exit_flag = Value('h', 0)

errors_queue  = Queue(maxsize=256)
