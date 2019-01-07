export class Transducer {
  private _dn: string;
  private _name: string;
  private _cid: string;
  private _objectClass: string;
  private _cstartEnabled: string;
  private _cstartConfig: string;
  private _ctype: string;
  private _creqAccess: string[];
  private _ou: string;


  constructor() {
  }


  get dn(): string {
    return this._dn;
  }

  set dn(value: string) {
    this._dn = value;
  }

  get name(): string {
    return this._name;
  }

  set name(value: string) {
    this._name = value;
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

  get cstartEnabled(): string {
    return this._cstartEnabled;
  }

  set cstartEnabled(value: string) {
    this._cstartEnabled = value;
  }

  get ctype(): string {
    return this._ctype;
  }

  set ctype(value: string) {
    this._ctype = value;
  }

  get cstartConfig(): string {
    return this._cstartConfig;
  }

  set cstartConfig(value: string) {
    this._cstartConfig = value;
  }

  get creqAccess(): string[] {
    return this._creqAccess;
  }

  set creqAccess(value: string[]) {
    this._creqAccess = value;
  }

  get ou(): string {
    return this._ou;
  }

  set ou(value: string) {
    this._ou = value;
  }
}
