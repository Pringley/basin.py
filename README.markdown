# Basin

Yet another task manager.

Tasks can live in states:

-   **`active`**: incomplete tasks

-   **`completed`**: done tasks

-   **`sleeping`**: deferred until later (can be indefinite)

-   **`delegated`**: delegated to someone else

-   **`blocked`**: requires completion of another task

-   **`trashed`**: deleted tasks

Tasks have the following properties:

-   **`tid`**: task id number

-   **`title`**: one-line description

-   **`completed`**: true/false, starts as false

-   **`project`**: true/false, is a high-level project, default false

-   **`due`**: due date (optional)

-   **`labels`**: descriptive tags (optional)

-   **`body`**: further description (optional)
