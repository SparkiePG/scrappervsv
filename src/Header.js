import React from 'react';

const Header = () => (
 <header className="bg-gray-800 text-white p-4">
      {/*
        The original className `-2xl` is not a valid Tailwind CSS utility. It
        should be `text-2xl` to control the font size. Without the `text-`
        prefix the negative sign is interpreted as part of the class name,
        leading to no styles being applied and confusing the build process.
      */}
      <h1 className="text-2xl font-bold">WebWhisper</h1>
 </header>
);

export default Header;
