export class Resource {
  private _dn: string;
  private _ccredentials: string;
  private _cid: string;
  private _objectClass: string;
  private _cunc: string;
  private _ctype: string;
  private _ou: string;


  constructor() {
  }


  get dn(): string {
    return this._dn;
  }

  set dn(value: string) {
    this._dn = value;
  }

  get ccredentials(): string {
    return this._ccredentials;
  }

  set ccredentials(value: string) {
    this._ccredentials = value;
  }

  get cid(): string {
    return this._cid;
  }

  set cid(value: string) {
    this._cid = value;
  }

  get objectClass(): string {
    return this._objectClass;
  }

  set objectClass(value: string) {
    this._objectClass = value;
  }

  get cunc(): string {
    return this._cunc;
  }

  set cunc(value: string) {
    this._cunc = value;
  }

  get ctype(): string {
    return this._ctype;
  }

  set ctype(value: string) {
    this._ctype = value;
  }

  get ou(): string {
    return this._ou;
  }

  set ou(value: string) {
    this._ou = value;
  }
}
