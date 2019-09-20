from multiprocessing import Queue, Value

input_queue   = Queue(maxsize=200)
predp_queue   = Queue(maxsize=200)
predict_queue = Queue(maxsize=200)
output_queue  = Queue(maxsize=200)

exit_flag = Value('h', 0)

errors_queue  = Queue(maxsize=256)
