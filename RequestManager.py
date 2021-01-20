import time
from Utils import *

class RequestManager:
    
    __requestqueue = []
    __signals = []
    
    
    def __init__(self):
        pass
    
    @classmethod
    def set_time_budget(cls,timems):
        cls.time_budget = timems
        cls.time_available = timems
    
    @classmethod 
    def add_request(cls,function,arguments, family = 'default',custom_priority_function = None, Duplicates_allowed = False ):
        #each request is appended as a tuple: function, arguments as a list, family of the reqyest, 
        #custom priority function and if duplicates entries are allowed 
        #check if the entry exist already, if it exists, do nothing
        can_add = True
        if not(Duplicates_allowed):
            for el in RequestManager.__requestqueue:
                if el[0]==function and el[1]==arguments:
                    can_add = False
                    break
        if can_add: RequestManager.__requestqueue.append((function,arguments,time.time(),family,custom_priority_function))
        
    @classmethod   
    def process_requests(cls):
        # check first element of the list. if its family is "default", process it. if its family is different, check against all other requests of the same family having lowest value of the custom_priority_function, and execute that one
        if RequestManager.__requestqueue:
            index = 0
            if RequestManager.__requestqueue[index][3] <> 'default':
                custom_family = RequestManager.__requestqueue[index][3]
                priority, indexp = min((el[4](),i) for (i,el) in enumerate(RequestManager.__requestqueue) if el[3]==custom_family)
                index = indexp
            t = time.time()*1000
            try:
                RequestManager.__requestqueue[index][0](*RequestManager.__requestqueue[index][1])
            except:
                print 'an exception had beenthrown byrequest manager'
            if (time.time()*1000-t > 200):
                print RequestManager.__requestqueue[index][0]
                print 't exec: '+str(time.time()*1000-t)
            #print RequestManager.__requestqueue.__len__()
            #print RequestManager.time_available
            del RequestManager.__requestqueue[index]

    @classmethod    
    def update(cls):
        t0 = time.time()
        #print('t aval'+str(RequestManager.time_available))
        while cls.time_available >= 0.0:
            cls.process_requests()
            dt = (time.time()-t0)*1000.0
            cls.time_available -=  dt
            t0 = time.time()
        if cls.time_available < 2*cls.time_budget:
            cls.time_available += cls.time_budget
            
    @classmethod        
    def get_queue_length(cls):
        return len(RequestManager.__requestqueue)
        
    @classmethod    
    def get_queue_max_wait_time_ms(cls):
        now = time.time()
        oldest_time = now
        for el in RequestManager.__requestqueue:
            if el[2] < oldest_time: oldest_time = el[2] 
        return (now-oldest_time)*1000.0
        
    @classmethod
    def get_time_available(cls):
        return cls.time_available