export class Application {
  private _dn: string;
  private _ou: string;
  private _cid: string;
  private _objectClass: string;
  private _cos: string;
  private _name: string;
  private _cport: string;
  private _cversion: string;

  constructor() {
  }

  get dn(): string {
    return this._dn;
  }

  set dn(value: string) {
    this._dn = value;
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

  get cos(): string {
    return this._cos;
  }

  set cos(value: string) {
    this._cos = value;
  }

  get name(): string {
    return this._name;
  }

  set name(value: string) {
    this._name = value;
  }

  get cport(): string {
    return this._cport;
  }

  set cport(value: string) {
    this._cport = value;
  }

  get cversion(): string {
    return this._cversion;
  }

  set cversion(value: string) {
    this._cversion = value;
  }

  get ou(): string {
    return this._ou;
  }

  set ou(value: string) {
    this._ou = value;
  }
}
