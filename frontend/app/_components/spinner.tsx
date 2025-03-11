export default function Spinner() {
    return (
        <div className="flex justify-center items-center">
        <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M12 2c-1.1 0-2 .9-2 2v8h4V4c0-1.1-.9-2-2-2z"></path>
        </svg>
      </div>
    );
  }