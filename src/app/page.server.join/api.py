struct = wiz.model("struct")

def verify_server_code():
    server_code = wiz.request.query("server_code", True)
    server_code = server_code.strip().upper()

    server = struct.server.find_by_code(server_code)
    if not server:
        wiz.response.status(400, message="유효하지 않은 서버 코드입니다.")

    # 세션에 server_id 저장 (회원가입 시 사용)
    wiz.session.set(join_server_id=server['id'])
    wiz.session.set(join_server_name=server['name'])

    wiz.response.status(200, name=server['name'], id=server['id'])
