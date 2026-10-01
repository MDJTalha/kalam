from app.api.routes.auth import ResetPasswordRequest, ChangePasswordRequest
from pydantic import ValidationError
weak="a"*12
strong="a"*9+"A1!"
for model in (ResetPasswordRequest, ChangePasswordRequest):
    try:
        if model is ResetPasswordRequest:
            model(token="x"*36,new_password=weak)
        else:
            model(current_password="x"*8,new_password=weak)
    except ValidationError:
        print(model.__name__+"_WEAK_REJECT=PASS")
    if model is ResetPasswordRequest:
        model(token="x"*36,new_password=strong)
    else:
        model(current_password="x"*8,new_password=strong)
    print(model.__name__+"_STRONG_ACCEPT=PASS")
