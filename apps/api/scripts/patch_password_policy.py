from pathlib import Path
p=Path(r"C:\Projects\CorpLMS\apps\api\app\api\routes\auth.py")
s=p.read_text()
start=s.index("class ResetPasswordRequest(BaseModel):")
end=s.index("class AuthDiscovery(BaseModel):")
block='''def _validate_password_strength(value: str) -> str:
    if len(value) < 12:
        raise ValueError("Password must be at least 12 characters long")
    if len(value) > 128:
        raise ValueError("Password must not exceed 128 characters")
    if not any(c.islower() for c in value) or not any(c.isupper() for c in value) or not any(c.isdigit() for c in value) or not any(not c.isalnum() for c in value):
        raise ValueError("Password must include uppercase, lowercase, number, and special character")
    return value

class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return _validate_password_strength(value)

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return _validate_password_strength(value)

class InvitationAccept(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password_strength(value)

'''
p.write_text(s[:start]+block+s[end:])
print("UPDATED")
