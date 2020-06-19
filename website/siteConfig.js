/**
 * Copyright (c) 2017-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

// See https://docusaurus.io/docs/site-config for all the possible
// site configuration options.

// List of projects/orgs using your project for the users page.
const users = [
  {
    caption: 'User1',
    // You will need to prepend the image path with your baseUrl
    // if it is not '/', like: '/test-site/img/image.jpg'.
    image: '/img/delphix-logo-white.png',
    infoLink: 'https://www.delphix.com',
    pinned: true,
  },
];

const siteConfig = {
  title: 'Couchbase Plugin', // Title for your website.
  tagline: 'Virtualise couchbase data sets',
  url: 'https://delphix.github.io', // Your website URL
  baseUrl: '/couchbase-plugin/', // Base URL for your project */
  projectName: 'couchbase-plugin',
  organizationName: 'delphix',




  // For no header links in the top nav bar -> headerLinks: [],
  headerLinks: [
    {doc: 'Overview', label: 'Docs'},
    {page: 'help', label: 'Help'},
    { search: true },
  ],

  // If you have users set above, you add it here:


  /* path to images for header/footer */
  headerIcon: '/img/delphix-logo-white.png',
  footerIcon: '/img/delphix-logo-white.png',
  favicon: '/img/logo.png',



  /* Colors for website */
  colors: {
    primaryColor: 'dodgerblue',
    secondaryColor: 'red',
  },


  /* Custom fonts for website */

  fonts: {
    myFont: [
      'Times New Roman',
      "Serif"
    ],
    myOtherFont: [
      "-apple-system",
      "system-ui"
    ]
  },


  // This copyright info is used in /core/Footer.js and blog RSS/Atom feeds.
  copyright: `Copyright © ${new Date().getFullYear()} Delphix`,

  highlight: {
    // Highlight.js theme to use for syntax highlighting in code blocks.
    theme: 'default',
  },

  // Add custom scripts here that would be placed in <script> tags.
  scripts: ['https://buttons.github.io/buttons.js'],

  // On page navigation for the current documentation page.
  onPageNav: 'separate',
  // No .html extensions for paths.
  cleanUrl: true,

  // Open Graph and Twitter card images.
  ogImage: 'img/undraw_online.svg',


  // For sites with a sizable amount of content, set collapsible to true.
  // Expand/collapse the links and subcategories under categories.
   docsSideNavCollapsible: true,

  // Show documentation's last contributor's name.
   enableUpdateBy: false,

  // Show documentation's last update time.
   enableUpdateTime: true,

  // You may provide arbitrary config keys to be used as needed by your
  // template. For example, if you need your repo's URL...
//  repoUrl: 'https://github.com/delphix/couchbase-plugin',

  scrollToTop: true,

  defaultVersionShown: '1.0.0',



};

module.exports = siteConfig;
