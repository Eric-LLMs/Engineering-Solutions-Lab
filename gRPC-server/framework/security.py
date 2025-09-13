import base64
import hmac

def sign(sk: str, text: str) -> str:
    '''
    使用密钥进行签名
    @param sk: secret key
    @param text: 文本
    @return 签名
    '''
    hmaccode = hmac.new(bytes(sk, 'utf-8'), bytes(text, 'utf-8'), 'sha1').digest()
    rtn = base64.b64encode(hmaccode).decode('utf-8')
    return rtn
