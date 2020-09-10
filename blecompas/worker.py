import threading,logging

def worker(q, filename, type):
    """ Worker to collect data send by notifications"""
    if filename:
        file_storage = open(filename, 'w') # overwrite if exists
    else:
        file_storage = None
    name = threading.currentThread().getName()
    print ("Thread: {0} start get item from queue[current size = {1}] at time = {2} \n".format(name, q.qsize(), strftime('%H:%M:%S')))
    logging.debug("Thread: {0} start".format(name))
    while True:
        r=q.get()
        if r is None:
            logging.debug("Thread: {0} stop".format(name))
            print("quit")
            if file_storage:
                file_storage.close()
                file_storage = None
            break
        #print("queue out")
        #print(r)
        raw_values = r.get(type)
        if raw_values != None:
            if file_storage:
                file_storage.write(raw_values.as_tsv()+"\n")
                file_storage.flush() # write immediately
            else:
                print ("X,Y,Z " + raw_values.as_tsv())

        q.task_done()
