# -*- coding: utf-8 -*-


def smart_str(s, encoding='utf-8', errors='strict'):
    if not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeDecodeError:
            if isinstance(s, Exception):
                return ' '.join([smart_str(arg, encoding, errors) 
                                 for arg in s])
            return unicode(s).encoding(encoding, errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s
    
