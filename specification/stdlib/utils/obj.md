# Standard for lib/utils/obj.uts

Exports:
```ts
namespace Object
{
	(function) AddProperty(obj, name, value)
	(function) HasProperty(obj, name)
	(function) AddPropertySafe(obj, name, value)
	(function) DeAllocate(obj)
	(function) GetProperty(obj, name)
	(function) SetProperty(obj, name, value)
	(function) SetPropertySafe(obj, name, value, onsuccess, onfail)
	(function) GetPropertySafe(obj, name, onsuccess, onfail)
	(function) Properties(obj)

}
```

<br/>
<br/>

## Object -> dynamic object utilites
Behavior is undefined if functions are called with the wrong type of arguments passed. A segmentation fault will most likely occur. `name` is always a string, `obj` is always a dynamic object, and `value` can be any type. `onsuccess` and `onfail` are both callback functions, whose arguments are discussed in more detail in individual function specs.

### `Object.AddProperty(obj, name, value)`
Takes in a dynamic object `obj`, a new property `name` (as a string), and a `value` to assign to that property. `AddProperty` should return a new dynamic object that is identical to the old object (having the same properties and values), except in the fact that the returned object will contain the new property `name` with the value of `value`. Behavior is undefined if the property `name` already exists on the object.

### `Object.HasProperty(obj, name)`
Takes in an dynamic object `obj` and a string `name`. Returns 1 (true) if the property `name` exists on the object and 0 (false) otherwise.

### `Object.AddPropertySafe(obj, name, value)`
Behaves exactly the same as `AddProperty(obj, name, value)`, but if the property `name` already exists on the object, the function does nothing and returns the original object.

### `Object.DeAllocate(obj)`
Takes in a dynamic object `obj` and cleans up and frees all memory being used by the object, effectively deleting it. Returns 0 on success.

### `Object.GetProperty(obj, name)`
Calls the get method of the object or otherwise somehow returns the value of property `name` of `obj`.

### `Object.SetProperty(obj, name value)`
Calls the set method of the object `obj` or otherwise somehow sets the property `name` to the value of `value`. If the property `name` doesn't exist, the function does nothing.

### `Object.SetPropertySafe(obj, name, value, onsuccess, onfail)`
If `obj` contains the property `name`, then `value` is assigned to `obj.{name}` and `onsuccess` is called with the object as the only argument. Otherwise, `onfail` is called with the object as the only argument. The return value of the function is the return value of whichever callback was called.

### `Object.GetPropertySafe(obj, name, onsuccess, onfail)`
If `obj` contains the property `name`, then `onsuccess` is called with `obj` and the value of `obj.{name}` (the property value). Otherwise, `onfail` is called with the object as the only argument. The return value of the function is the return value of whichever callback was called.

### `Object.Properties(obj)`
Returns an array, probably dynamically allocated (but this is up to implementation), that contains all of `obj`'s property names (as strings).