const fs = require('fs');

// Patch synchronous fs.readlinkSync
const origReadlinkSync = fs.readlinkSync;
fs.readlinkSync = function(path, options) {
  try {
    return origReadlinkSync.apply(this, arguments);
  } catch (err) {
    if (err && (err.code === 'EISDIR' || err.code === 'EINVAL')) {
      const e = new Error('EINVAL: invalid argument, readlink');
      e.code = 'EINVAL';
      throw e;
    }
    throw err;
  }
};

// Patch callback fs.readlink
const origReadlink = fs.readlink;
fs.readlink = function(path, options, callback) {
  if (typeof options === 'function') {
    callback = options;
    options = {};
  }
  origReadlink.call(this, path, options, (err, linkString) => {
    if (err && (err.code === 'EISDIR' || err.code === 'EINVAL')) {
      const e = new Error('EINVAL: invalid argument, readlink');
      e.code = 'EINVAL';
      return callback(e);
    }
    callback(err, linkString);
  });
};

// Patch promises fs.promises.readlink
if (fs.promises && fs.promises.readlink) {
  const origPromisesReadlink = fs.promises.readlink;
  fs.promises.readlink = async function(path, options) {
    try {
      return await origPromisesReadlink.apply(this, arguments);
    } catch (err) {
      if (err && (err.code === 'EISDIR' || err.code === 'EINVAL')) {
        const e = new Error('EINVAL: invalid argument, readlink');
        e.code = 'EINVAL';
        throw e;
      }
      throw err;
    }
  };
}
