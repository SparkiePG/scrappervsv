import React from 'react';

// This component renders a preview of the scraped data.  It uses a padded
// container and formats the data as pretty‑printed JSON.  The comment
// regarding Tailwind classes has been moved above the return statement to
// avoid interfering with JSX parsing.
const ResultsPreview = ({ data }) => {
  /*
   * The padding class `p-` in the original version was incomplete.  Tailwind
   * utility classes for padding require a suffix such as `p-4` to specify
   * the spacing value.  Without a suffix the class name is invalid and
   * Next.js will fail to compile.  We use `p-4` here to apply a reasonable
   * default padding to the container.
   */
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-2">Scraped Data</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};

export default ResultsPreview;
