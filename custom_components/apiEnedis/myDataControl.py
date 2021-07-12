try:
    from .const import (
        __nameMyEnedis__,
    )

except ImportError:
    from const import (
        __nameMyEnedis__,
    )

import logging
log = logging.getLogger(__nameMyEnedis__)

def okDataControl( clefFunction, dataControl, dateDeb, dateFin, ):
    log.info("--okDataControl--")
    log.info("--okDataControl / clefFunction : %s" %clefFunction )
    log.info("--okDataControl / deb : %s / %s" %(dataControl.get('deb', None), dateDeb) )
    log.info("--okDataControl / fin : %s / %s" %(dataControl.get('fin', None), dateFin) )
    log.info("--okDataControl / callok : %s " %(dataControl.get('callok', True)) )
    deb = dataControl.get('deb', None)
    fin = dataControl.get('fin', None )
    callOk = dataControl.get('callok', True)
    if ( callOk == None):
        callOk = True
    response = ( deb == dateDeb and fin == dateFin and callOk )
    return response