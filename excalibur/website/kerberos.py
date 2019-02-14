import pexpect
import time

class Kerberos:
    def generate_tgt(self, username, password):
        child = pexpect.spawn("kinit -c /tmp/krb5cc_" + username + " " + username)
        child.expect("Password for .*:")
        child.sendline(password)
        child.expect(pexpect.EOF)

    def destroy_tgt(self, username):
        child = pexpect.spawn("kdestroy -c /tmp/krb5cc_" + username)
        child.expect(pexpect.EOF)

if __name__ == "__main__":
    krb = Kerberos()
    krb.generate_tgt("klittle", "Test123!")
    time.sleep(5)
    krb.destroy_tgt("klittle")
