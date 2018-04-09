function login(e: any) {
  let msg: string = '';
  let color: string = 'admin';
  let id: string = (document.getElementById('userId') as HTMLInputElement).value;
  let pw: string = (document.getElementById('password')as HTMLInputElement).value;
  let loginMsg: HTMLElement = document.getElementById('loginMsg');
  let login: HTMLElement = document.getElementById('login');
  let dockWrapper: HTMLElement  = document.getElementById('dockWrapper');

  // Ignore unless user pressed enter in pwd field OR clicked submit button
  if (e.type === 'keypress' && e.charCode === 13 || e.type === 'click') {
    if(id === ''){
      msg = 'Please enter your ID';
    } else if (pw === '') {
      msg = 'Please enter your password';
    // TODO Handle real auth
    } else {
      if (id === 'test' && pw === 'test123') {
        // Authenticated
        login.classList.remove('fadeIn');
        login.classList.add('fadeOut');
        setTimeout( function() {
          login.parentElement.removeChild(login);
        }, 300);
        dockWrapper.style.display = 'flex';
        msg = 'Welcome';
        color = 'viewer';
      } else {
        msg = 'ID and/or Password Incorrect';
      }
    }
  }

  loginMsg.innerHTML = msg;
  loginMsg.className = ''; // Clear out old color
  loginMsg.classList.add(color);
}
