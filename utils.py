
def is_input_int(val = None, min = None, max =None):
    try:
        if int(val) == val and min<=val<=max:
            return True
    except:
        return False


def input_int(min , max, val = None):
    while True:
        try:
            if is_input_int(val, min, max):
                return val
        except:
            val= input(f"Invalid input. Try again.")


def can_be_number(x): #if the number can't be converted it means that is is not a number
    try:
        float(x)
        return True
    except:
        return False

def is_type_number(x): #test type of number
    return type(x)==float or type(x)==int