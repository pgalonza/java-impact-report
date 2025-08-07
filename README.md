# Impact report for Java monolith project(Example)

The report provides information about which business processes have been impacted by package and module changes.

The information is stored in the package-info.java file, which is searched for if the package has been modified, and the description is extracted from this file.

Script logic:
1. We compare the current branch with the master branch to find the differences.
2. We save the names of modified modules and paths to modified files in those modules.
3. We recursively search for the "package-info.java" file in the repository structure, starting from the directory containing the modified file. The file may not be in the package itself, so we search the entire module for it.
4. Once the file is found, we fully read its contents and extract the text between "<AI></AI>" tags, formatting it for readability.
5. This data is then saved for further processing by the template engine to create a visualization report.

The report can include:
- The name of the module that has been modified
- Names of packages and files within the module that have been changed
- An explanation of what processes these changes impact
