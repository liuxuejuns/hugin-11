import time
import multiprocessing

SEQUENCE_BITS = 12

SEQUENCE_MASK = -1 ^ (-1 << SEQUENCE_BITS)  # 4095


class SnowFlake:
    
    last_pk = 0
    seq = 0

    def __init__(self) -> None:
        pass

    @staticmethod
    def get_time():
        return time.time()*10000000

    @classmethod
    def get_pk(cls):
        pk = SnowFlake.get_time()
        if pk == cls.last_pk:
            cls.seq = (cls.seq + 1) & SEQUENCE_MASK
            # 瞬间并发量超过4095个
            if cls.seq == 0:
                pk = cls._next_pk()
        elif pk < cls.last_pk:
            raise InvalidSystemClock("The clock rollback is abnormal")
        else:
            cls.seq = 0 # 回到初始状态
        # 时间戳长度为21/22，计算后序列号长度22/23
        cls.last_pk = pk
        # 目前雪花 = 时间戳 + 偏移序列号
        # 以后雪花 = 时间戳 + 服务器ID + 测试机台ID + 偏移序列号
        pk = (int(pk) << 12) ^ cls.seq
        
        return pk

    @classmethod
    def _next_pk(cls):
        '''
        获取下一秒时间戳
        '''
        pk = SnowFlake.get_time()
        while pk <= cls.last_pk:
            pk = SnowFlake.get_time()
        return pk

        

class InvalidSystemClock(Exception):
    """
    时钟回拨异常
    """
    pass